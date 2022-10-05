import os
import sys
import time

from scrapy import Request

from scrapy_tplp_demos.components.utils.secure import SecureUtil, Base64

sys.path.append(os.path.abspath(r'../..'))

from datetime import datetime

from dateutil.tz import tz
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from scrapy_tplp_demos.components.utils.parser import ResponseParser
from scrapy_tplp_demos.items import ScrapyTplpDemosItemLoader


# from datetime import datetime, timedelta
# from dateutil.tz import tz
# from scrapy.linkextractors import LinkExtractor
# from scrapy_tplp_demos.components.middlewares.aiohttpcrawl import AiohttpRequest
# from scrapy_tplp_demos.components.middlewares.seleniumcrawl import SeleniumRequest

# class Spa2Spider(RedisSpider):
class Spa2Spider(CrawlSpider):
    name = 'spa2'
    allowed_domains = ['scrape.center']

    # 链接参数加密，这里的 start_urls 就没啥用了 需要在 start_requests 方法实现
    # start_urls = [
    #     'https://spa2.scrape.center/',
    # ]

    # 计算token的方法
    def get_token(self, path, page):
        a = (page - 1) * 10
        t = int(time.time())
        r = F'{path},{a},{t}'
        o = SecureUtil.sha1(r)
        c = Base64.encode(F'{o},{t}')
        return c

    def start_requests(self):
        # 爬前三页数据
        for i in range(3):
            url = F'https://spa2.scrape.center/api/movie/?limit=10&offset={i * 10}&token={self.get_token("/api/movie", i + 1)}'
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        # 解析列表页中的文章也链接，也需要计算token
        n = 'ef34#teuq0btua#(-57w1q5o5--j@98xygimlyfxs*-!i-0-mb'
        detail_list = ResponseParser(response).jsonpath('$.results[*].id').get()
        for detail in detail_list:
            detail_url = Base64.encode(n + str(detail))
            token = self.get_token(F"/api/movie/{detail_url}", 1)
            url = F'https://spa2.scrape.center/api/movie/{detail_url}/?token={token}'
            yield Request(url=url, callback=self.parse_item)

    def parse_item(self, response, **kwargs):
        create_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        update_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        # parse_json 来解析列表页字段
        return ScrapyTplpDemosItemLoader().parse_json(ResponseParser(response),
                                                      create_time=create_time,
                                                      update_time=update_time)


if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(Spa2Spider)
    process.start()
