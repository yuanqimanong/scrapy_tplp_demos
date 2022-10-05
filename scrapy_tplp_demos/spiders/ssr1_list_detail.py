import os
import sys

sys.path.append(os.path.abspath(r'../..'))

from datetime import datetime

from dateutil.tz import tz
from scrapy import Request
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from scrapy_tplp_demos.components.utils import CommonUtil
from scrapy_tplp_demos.components.utils.parser import ResponseParser
from scrapy_tplp_demos.items import ScrapyTplpDemosItemLoader


# from datetime import datetime, timedelta
# from dateutil.tz import tz
# from scrapy.linkextractors import LinkExtractor
# from scrapy_tplp_demos.components.middlewares.aiohttpcrawl import AiohttpRequest
# from scrapy_tplp_demos.components.middlewares.seleniumcrawl import SeleniumRequest

# class Ssr1ListDetailSpider(RedisSpider):
class Ssr1ListDetailSpider(CrawlSpider):
    name = 'ssr1_list_detail'
    allowed_domains = ['scrape.center']

    start_urls = [
        'https://ssr1.scrape.center/',
        'https://ssr1.scrape.center/page/【10-2:1】',
    ]

    def start_requests(self):
        urls = CommonUtil.turn_page(self.start_urls)
        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        links = LinkExtractor(allow=(r'detail/\d+',), deny=(),
                              restrict_xpaths=('//div[@class="el-col el-col-18 el-col-offset-3"]',)).extract_links(
            response)
        for link in links:
            yield Request(url=link.url, callback=self.parse_item)

    def parse_item(self, response, **kwargs):
        create_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        update_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        return ScrapyTplpDemosItemLoader().parse_item(ResponseParser(response),
                                                      create_time=create_time,
                                                      update_time=update_time)


if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(Ssr1ListDetailSpider)
    process.start()
