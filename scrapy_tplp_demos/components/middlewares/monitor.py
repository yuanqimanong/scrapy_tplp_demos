import time
import traceback

from scrapy.exceptions import NotConfigured
from scrapy.spidermiddlewares.httperror import HttpError

from scrapy_tplp_demos.components.utils import CommonUtil
from scrapy_tplp_demos.components.utils.dingding import DingDingRobot


class ExceptionSpiderMiddleware:

    def __init__(self, monitor_log, monitor_dingding_web_hook, monitor_dingding_secret, monitor_dingding_at_mobiles):
        self.monitor_log = monitor_log
        CommonUtil.mk_dir(self.monitor_log)
        self.ding_talk = None
        if '' != monitor_dingding_web_hook and '' != monitor_dingding_secret:
            self.ding_talk = DingDingRobot(monitor_dingding_web_hook, monitor_dingding_secret)
            self.monitor_dingding_at_mobiles = monitor_dingding_at_mobiles

    @classmethod
    def from_crawler(cls, crawler):
        monitor_log = crawler.settings.get('MONITOR_LOG') or ''
        if '' != monitor_log:
            monitor_dingding_web_hook = crawler.settings.get('MONITOR_DINGDING_WEB_HOOK') or ''
            monitor_dingding_secret = crawler.settings.get('MONITOR_DINGDING_SECRET') or ''
            monitor_dingding_at_mobiles = list(
                str(x) for x in crawler.settings.get('MONITOR_DINGDING_AT_MOBILES') or [])
            return cls(monitor_log, monitor_dingding_web_hook, monitor_dingding_secret, monitor_dingding_at_mobiles)
        raise NotConfigured(
            '请先设置【监控日志的存储路径】及钉钉机器人的【WebHook】和【secret】！（MONITOR_LOG、MONITOR_DINGDING_WEB_HOOK、MONITOR_DINGDING_SECRET）')

    def process_spider_exception(self, response, exception, spider):
        if not isinstance(exception, HttpError):
            error_count = spider.crawler.stats.get_value(F'spider_error/{exception}', default=0)
            spider.crawler.stats.inc_value(F'spider_error/{exception}')
            if error_count == 0:
                error_info = "".join(traceback.format_exception(exception, exception, exception.__traceback__))
                msg = F'''【实时预警】
{spider.settings.get("SPIDER_MODULES")[0]} - {spider.name} 在 [ {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} ] 时发生异常！
<异常网址> \n {response.url}
<异常定位> \n {error_info}
'''

                if self.ding_talk:
                    self.ding_talk.send_msg(msg, self.monitor_dingding_at_mobiles)

                with open(self.monitor_log, "a+", encoding="utf-8") as f:
                    f.write(F'{msg}\n')
                return []


class ExceptionMiddleware:

    def __init__(self, monitor_log, monitor_dingding_web_hook, monitor_dingding_secret, monitor_dingding_at_mobiles):
        self.monitor_log = monitor_log
        CommonUtil.mk_dir(self.monitor_log)
        self.ding_talk = None
        if '' != monitor_dingding_web_hook and '' != monitor_dingding_secret:
            self.ding_talk = DingDingRobot(monitor_dingding_web_hook, monitor_dingding_secret)
            self.monitor_dingding_at_mobiles = monitor_dingding_at_mobiles

    @classmethod
    def from_crawler(cls, crawler):
        monitor_log = crawler.settings.get('MONITOR_LOG') or ''
        if '' != monitor_log:
            monitor_dingding_web_hook = crawler.settings.get('MONITOR_DINGDING_WEB_HOOK') or ''
            monitor_dingding_secret = crawler.settings.get('MONITOR_DINGDING_SECRET') or ''
            monitor_dingding_at_mobiles = list(
                str(x) for x in crawler.settings.get('MONITOR_DINGDING_AT_MOBILES') or [])
            return cls(monitor_log, monitor_dingding_web_hook, monitor_dingding_secret, monitor_dingding_at_mobiles)
        raise NotConfigured(
            '请先设置【监控日志的存储路径】及钉钉机器人的【WebHook】和【secret】！（MONITOR_LOG、MONITOR_DINGDING_WEB_HOOK、MONITOR_DINGDING_SECRET）')

    def process_exception(self, request, exception, spider):
        if not isinstance(exception, HttpError):
            error_count = spider.crawler.stats.get_value(F'spider_error/{exception}', default=0)
            spider.crawler.stats.inc_value(F'spider_error/{exception}')
            if error_count == 0:
                error_info = "".join(traceback.format_exception(exception, exception, exception.__traceback__))
                msg = F'''【实时预警】
{spider.settings.get("SPIDER_MODULES")[0]} - {spider.name} 在 [ {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} ] 时发生异常！
<异常网址> \n {request.url}
<异常定位> \n {error_info}
'''

                if self.ding_talk:
                    self.ding_talk.send_msg(msg, self.monitor_dingding_at_mobiles)

                with open(self.monitor_log, "a+", encoding="utf-8") as f:
                    f.write(F'{msg}\n')
                return []
