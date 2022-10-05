import asyncio

import aiohttp
import cchardet
from aiohttp import ClientTimeout, ClientConnectionError
from anti_useragent.utils.cipers import sslgen
from scrapy import Request, signals
from scrapy.http import HtmlResponse
from scrapy.utils.request import request_httprepr

from scrapy_tplp_demos.components.utils import CommonUtil


class AiohttpRequest(Request):
    def __init__(self, url, params=None, aiohttp_data=None, aiohttp_json=None, *args, **kwargs):
        self.params = params
        self.aiohttp_data = aiohttp_data
        self.aiohttp_json = aiohttp_json
        super().__init__(url, *args, **kwargs)


class AiohttpCrawlMiddleware:
    EXCEPTIONS_TO_RETRY = (ClientConnectionError,)

    def __init__(self, stats):
        self.stats = stats
        self.loop = asyncio.get_event_loop()
        self.client = aiohttp.ClientSession(loop=self.loop, connector=aiohttp.TCPConnector(ssl=False))

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.stats)
        crawler.signals.connect(o.spider_closed, signals.spider_closed)
        return o

    async def process_request(self, request, spider):
        if isinstance(request, AiohttpRequest):
            # 记录状态
            self.stats.inc_value('downloader/request_count', spider=spider)
            self.stats.inc_value(F'downloader/request_method_count/{request.method}', spider=spider)
            self.stats.inc_value('downloader/request_bytes', len(request_httprepr(request)), spider=spider)

            # 获取代理
            proxy = request.meta.get("proxy") or ''

            async with self.client.request(
                    method=request.method,
                    url=request.url,
                    params=request.params,
                    headers=CommonUtil.convert_headers(request.headers),
                    data=request.aiohttp_data,
                    json=request.aiohttp_json,
                    timeout=ClientTimeout(total=request.meta.get('download_timeout')),
                    proxy=proxy,
                    ssl=sslgen(),
            ) as resp:
                body = await resp.read()
                headers = resp.headers
                encoding = cchardet.detect(body)['encoding']
                response = HtmlResponse(request.url,
                                        status=resp.status,
                                        headers=headers,
                                        body=body,
                                        request=request,
                                        encoding=encoding)
                content_encoding = response.headers.getlist('Content-Encoding')
                if content_encoding:
                    del response.headers['Content-Encoding']
                return response

    async def spider_closed(self):
        await self.client.close()
