# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import re

import scrapy
from scrapy.loader import ItemLoader
from scrapy.utils.request import request_fingerprint

from scrapy_tplp_demos.components.utils.secure import SecureUtil


class ScrapyTplpDemosItem(scrapy.Item):
    # 指纹，主键
    id = scrapy.Field()
    # 网址
    url = scrapy.Field()
    # 影片名称
    name = scrapy.Field()
    # 别名
    alias = scrapy.Field()
    # 类别
    categories = scrapy.Field()
    # 上映地区
    regions = scrapy.Field()
    # 影片时长
    minute = scrapy.Field()
    # 上映时间
    published_at = scrapy.Field()
    # 封面
    cover = scrapy.Field()
    # 评分
    score = scrapy.Field()
    # 级别
    rank = scrapy.Field()
    # 剧情
    drama = scrapy.Field()
    # 导演
    directors = scrapy.Field()
    # 演员
    actors = scrapy.Field()
    # 剧照
    photos = scrapy.Field()

    # 抓取时间
    create_time = scrapy.Field()
    # 更新时间
    update_time = scrapy.Field()


# See documentation in:
# https://docs.scrapy.org/en/latest/topics/loaders.html
class ScrapyTplpDemosItemLoader(ItemLoader):

    @classmethod
    def parse_item(cls, response, **kwargs):
        item = ScrapyTplpDemosItem()
        # 用request_fingerprint计算url的指纹，作为主键
        item['id'] = SecureUtil.md5(request_fingerprint(response.request))
        # 正则提取
        item['url'] = response.url
        item['name'] = response.selector.re_first(r'<h2 [^>]*?class="m-b-sm">(.*?)\s+-\s+.*?</h2>')
        item['alias'] = response.selector.re_first(r'<h2 [^>]*?class="m-b-sm">.*?\s+-\s+(.*?)</h2>')
        item['categories'] = response.xpath('//div[@class="categories"]//span/text()').getall()
        # XPath
        item['regions'] = response.xpath('//div[@class="m-v-sm info"]//span[1]/text()').get().split('、')
        # XPath + 正则
        item['minute'] = response.xpath('//div[@class="m-v-sm info"]//span[3]/text()').re_first(r'(\d+)')
        item['published_at'] = response.xpath('//div[@class="m-v-sm info"][2]//span/text()').re_first(
            r'(\d{4}-\d{1,2}-\d{1,2})')

        item['cover'] = response.xpath('//img[@class="cover"]/@src').get()
        item['score'] = response.xpath('//p[@class="score m-t-md m-b-n-sm"]/text()').get(default='').strip()

        item['drama'] = response.selector.re_first(
            r'<h3 data-v-63864230="">剧情简介</h3>\s*<p[^>]*?>([\D\d]*?)</p>').strip()

        item['directors'] = response.xpath('//div[@class="directors el-row"]//p/text()').getall()
        # 列表推导式
        actors_list = response.xpath('//div[@class="actors el-row"]//div[@class="el-card__body"]')
        item['actors'] = {actors.xpath('.//p[contains(@class,"name")]/text()').get():
                              actors.xpath('.//p[contains(@class,"role")]/text()').get().replace('饰：', '')
                          for actors in actors_list
                          }
        item['photos'] = response.xpath('//div[@class="photos el-row"]//img/@src').getall()

        item['create_time'] = kwargs['create_time']
        item['update_time'] = kwargs['update_time']
        return item

        #####################
        #  ItemLoader 写法  #
        ####################

        # item = ItemLoader(item=ScrapyTplpDemosItem(), response=response)
        # # 默认输出首个结果
        # item.default_output_processor = TakeFirst()
        #
        # item.add_value('id', SecureUtil.md5(request_fingerprint(response.request))))
        # item.add_value('urlname', response.url)
        # item.add_xpath('title', '//h1')
        # item.add_value('create_time', kwargs['create_time'])
        # item.add_value('update_time', kwargs['update_time'])
        # return item.load_item()

    @classmethod
    def parse_list(cls, response, **kwargs):
        group_list = response.selector.re(r'(<div class="el-card__body">[\D\d]*?</div>\s*</div>\s*</div>)\s*</div>')
        for group in group_list:
            item = ScrapyTplpDemosItem()
            # 用request_fingerprint计算url的指纹，作为主键
            # 但这个在同一页面提取多条数据的模式 url是一致，需要增加区别点一并计算主键，这里是 列表url+name+published_at
            name = re.search(r'<h2 [^>]*?class="m-b-sm">(.*?)</h2>', group).group(1)
            published_at_result = re.search(r'<div [^>]*?class="m-v-sm info">\s*<span.*?>(.*?) 上映</span>', group)
            published_at = ''
            if published_at_result is not None:
                published_at = published_at_result.group(1)

            item['id'] = SecureUtil.md5(request_fingerprint(response.request) + name + published_at)

            item['url'] = response.url
            item['name'] = name.split(' - ')[0]
            item['alias'] = name.split(' - ')[1]
            item['categories'] = re.findall(r'<span>(.*?)</span>', re.search(
                r'<div [^>]*?class="categories">([\D\d]*?)<div [^>]*?class="m-v-sm info">', group).group(1))

            item['regions'] = re.sub(r'<[^>]*?>|\s', '',
                                     re.search(r'<div [^>]*?class="m-v-sm info">([\D\d]*?)</span>', group).group(
                                         1)).split('、')

            item['minute'] = re.search(
                r'<div [^>]*?class="m-v-sm info">[\D\d]*?</span>[\D\d]*?</span>\s*<span[^>]*?>(\d+) 分钟</span>',
                group).group(1)

            item['published_at'] = published_at

            item['cover'] = re.search(r'<img[^>]*?src="([^>]*?)"\s*class="cover">', group).group(1)
            item['score'] = re.search(r'<p [^>]*?class="score m-t-md m-b-n-sm">\s*(\S*?)</p>', group).group(1)

            item['create_time'] = kwargs['create_time']
            item['update_time'] = kwargs['update_time']
            yield item

    @classmethod
    def parse_json(cls, response, **kwargs):
        item = ScrapyTplpDemosItem()
        item['id'] = SecureUtil.md5(request_fingerprint(response.request))
        item['url'] = response.url

        # jsonpath 写法
        item['name'] = response.jsonpath('$.name').get()
        item['alias'] = response.jsonpath('$.alias').get()
        item['categories'] = response.jsonpath('$.categories').get()
        item['regions'] = response.jsonpath('$.regions').get()
        item['minute'] = response.jsonpath('$.minute').get()
        item['published_at'] = response.jsonpath('$.published_at').get()
        item['cover'] = response.jsonpath('$.cover').get()
        item['score'] = response.jsonpath('$.score').get()
        item['rank'] = response.jsonpath('$.rank').get()
        item['drama'] = response.jsonpath('$.drama').get()
        item['directors'] = response.jsonpath('$.directors').get()
        item['actors'] = response.jsonpath('$.actors').get()
        item['photos'] = response.jsonpath('$.photos').get()

        item['create_time'] = kwargs['create_time']
        item['update_time'] = kwargs['update_time']
        return item
