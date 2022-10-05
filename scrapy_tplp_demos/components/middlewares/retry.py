from logging import getLogger, Logger
from typing import Optional, Union

from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse, Response
from scrapy.http.request import Request
from scrapy.spiders import Spider
from scrapy.utils.python import global_object_name
from scrapy.utils.response import response_status_message
from twisted.internet import defer
from twisted.internet.error import (
    ConnectError,
    ConnectionDone,
    ConnectionLost,
    ConnectionRefusedError,
    DNSLookupError,
    TCPTimedOutError,
    TimeoutError,
)
from twisted.web.client import ResponseFailed

from scrapy_tplp_demos.components.middlewares.blacklist import RetryBanListChecker
from scrapy_tplp_demos.components.utils import CommonUtil

retry_logger = getLogger(__name__)


def get_retry_request(
        request: Request,
        *,
        spider: Spider,
        reason: Union[str, Exception] = 'unspecified',
        max_retry_times: Optional[int] = None,
        priority_adjust: Optional[int] = None,
        logger: Logger = retry_logger,
        stats_base_key: str = 'retry',
):
    settings = spider.crawler.settings
    stats = spider.crawler.stats
    retry_times = request.meta.get('retry_times', 0) + 1
    if max_retry_times is None:
        max_retry_times = request.meta.get('max_retry_times')
        if max_retry_times is None:
            max_retry_times = settings.getint('RETRY_TIMES')
    if retry_times <= max_retry_times:
        logger.debug(
            "Retrying %(request)s (failed %(retry_times)d times): %(reason)s",
            {'request': request, 'retry_times': retry_times, 'reason': reason},
            extra={'spider': spider}
        )
        new_request: Request = request.copy()
        new_request.meta['retry_times'] = retry_times
        new_request.dont_filter = True
        if priority_adjust is None:
            priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')
        new_request.priority = request.priority + priority_adjust

        if callable(reason):
            reason = reason()
        if isinstance(reason, Exception):
            reason = global_object_name(reason.__class__)

        stats.inc_value(f'{stats_base_key}/count')
        stats.inc_value(f'{stats_base_key}/reason_count/{reason}')
        return new_request
    else:
        stats.inc_value(f'{stats_base_key}/max_reached')
        logger.error(
            "Gave up retrying %(request)s (failed %(retry_times)d times): "
            "%(reason)s",
            {'request': request, 'retry_times': retry_times, 'reason': reason},
            extra={'spider': spider},
        )
        return HtmlResponse(url=request.url,
                            body='',
                            encoding='utf-8',
                            request=request,
                            status=-1)


class RetryLogMiddleware:
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        if not settings.getbool('RETRY_ENABLED'):
            raise NotConfigured
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

        self.retry_log = settings.get('RETRY_LOG') or ''
        self.retry_log_404 = settings.get('RETRY_LOG_404') or ''
        self.retry_log_ban = settings.get('RETRY_LOG_BAN') or ''

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False) or -1 == response.status:
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response

        # 记录404的链接，格式：网址\t源码长度，源码长度大说明有可能是故意返回404状态码的反爬措施
        if '' != self.retry_log_404 and 404 == response.status:
            CommonUtil.mk_dir(self.retry_log_404)
            with open(self.retry_log_404, "a+", encoding="utf-8") as f:
                f.write(F'{request.url}\t{len(response.text)}\n')
        # 记录禁止访问的链接
        if '' != self.retry_log_ban and hasattr(response, 'text'):
            if RetryBanListChecker.judgement(response.text):
                CommonUtil.mk_dir(self.retry_log_ban)
                with open(self.retry_log_ban, "a+", encoding="utf-8") as f:
                    f.write(F'{request.url}\n')
        return response

    def process_exception(self, request, exception, spider):
        if (
                isinstance(exception, self.EXCEPTIONS_TO_RETRY)
                and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        max_retry_times = request.meta.get('max_retry_times', self.max_retry_times)
        priority_adjust = request.meta.get('priority_adjust', self.priority_adjust)
        result = get_retry_request(
            request,
            reason=reason,
            spider=spider,
            max_retry_times=max_retry_times,
            priority_adjust=priority_adjust,
        )
        # 重试到最大次数依旧失败的情况，记录一下
        if isinstance(result, Response):
            if '' != self.retry_log and -1 == result.status:
                CommonUtil.mk_dir(self.retry_log)
                with open(self.retry_log, "a+", encoding="utf-8") as f:
                    f.write(F'{request.url}\n')
        return result
