# scrapy-template-plus demo

> 本项目提供了该模板一些基础写法的样例和讲解，方便大家快速实现爬虫，避免重复造轮子



## Demo 0

> 下载好`scrapy-template-plus`项目后，
>
> 安装依赖（`pip install -r requirements.txt`），
>
> 运行`builder-run.py`。
>
> 按操作提示，生成的项目为抓取 ["http://books.toscrape.com/"](http://books.toscrape.com/)地址前5页数据。
>
> 可以测试项目是否生成正确。



## Demo 1 列表页→文章页

> 本项目中`spiders`目录下的`ssr1_list_detail.py`是对于["https://ssr1.scrape.center/"](https://ssr1.scrape.center/)地址的爬虫
>
> 主要采集逻辑是采集首页和第10、11页的数据，通过 列表页分析文章页链接，进而抓取文章页字段，再进行存储的过程

P.S. 本案例用的是《Python3网络爬虫开发实战（第二版）》配套案例，本人已购入，非常值得一看，推荐

### ssr1_list_detail.py

```python
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

## 该区域注释 用于方便导库
# from datetime import datetime, timedelta
# from dateutil.tz import tz
# from scrapy.linkextractors import LinkExtractor
# from scrapy_tplp_demos.components.middlewares.aiohttpcrawl import AiohttpRequest
# from scrapy_tplp_demos.components.middlewares.seleniumcrawl import SeleniumRequest

# 方便修改成 ScrapyRedis项目，还需要修改settings.py文件【Scrapy-Redis】设置
# class Ssr1ListDetailSpider(RedisSpider):
class Ssr1ListDetailSpider(CrawlSpider):
    name = 'ssr1_list_detail'
    allowed_domains = ['scrape.center']
	
    # 放入采集种子URL列表
    start_urls = [
        'https://ssr1.scrape.center/',
        'https://ssr1.scrape.center/page/【10-2:1】',
    ]

    def start_requests(self):
        # CommonUtil.turn_page() 是对'https://ssr1.scrape.center/page/【10-2:1】'翻页参数的解析
        # 约定格式：【起始数字-爬行的页数:公差】，公差为1时可以写成【起始数字-爬行的页数】
        urls = CommonUtil.turn_page(self.start_urls)
        for url in urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        links = LinkExtractor(allow=(r'detail/\d+',), deny=(),
                              restrict_xpaths=('//div[@class="el-col el-col-18 el-col-offset-3"]',)).extract_links(
            response)
        for link in links:
            # 除了Scrapy的Request，还可以用AiohttpRequest（异步）、SeleniumRequest（Selenium自动化）
            yield Request(url=link.url, callback=self.parse_item)

    def parse_item(self, response, **kwargs):
        # 定义时区（考虑境外站点），依据业务而定
        create_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        update_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        # ResponseParser继承了response，增加了jsonpath表达式的支持，方便json解析
        # parse_item的目的是，将所有字段解析都交由items.py中处理
        return ScrapyTplpDemosItemLoader().parse_item(ResponseParser(response),
                                                      create_time=create_time,
                                                      update_time=update_time)


if __name__ == '__main__':
    # 启动爬虫入口
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(Ssr1ListDetailSpider)
    process.start()

```

### items.py

```python
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.utils.request import request_fingerprint

from scrapy_tplp_demos.components.utils.secure import SecureUtil

# 定义字段
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

```

### 运行调试下

> 完成以上就可以运行程序将数据采集到本机
>
> 存储位置在`spiders`目录下，`debug/data`的`txt`文件中
>
> `retry-log`存储的内容为：达到重试上限且仍然错误的url地址

### settings.py

> 这个配置可以简单看成5个部分，分别是：
>
> 1. 监控报告设置
> 2. 存储设置
> 3. 采集策略设置
> 4. 伪装策略设置
> 5. 中间件设置
>
> 前四个看成简单模式，最后一个可以自己定制中间件满足业务需求

#### 监控报告设置

> 监控、报告暂只支持钉钉机器人，填入`WEB_HOOK`、`SECRET`即可使用
>
> `AT_MOBILES`是`@某人`需要填入`某人的手机号`
>
> 当报告设置未填写时，都按照监控填写的内容执行

```python
'''
【监控】设置，MONITOR_LOG为监控日志存储路径，钉钉推送消息功能可为空
'''
MONITOR_LOG = F"./debug/monitor-log/{DEBUG_FILE_NAME}.txt"
# MONITOR_DINGDING_WEB_HOOK = ''
# MONITOR_DINGDING_SECRET = ''
# MONITOR_DINGDING_AT_MOBILES = []

'''
【报告】设置，不设置的话，默认为“监控设置”设置的钉钉信息
'''
# REPORT_DINGDING_WEB_HOOK = ''
# REPORT_DINGDING_SECRET = ''
# REPORT_DINGDING_AT_MOBILES = []
```

#### 存储设置

> 正如注释写的一样，填入地址就可以启用功能，若要彻底禁用需要关闭对应中间件
>
> 写多个表数据时，需要修改相应中间件代码
>
> DB_MODE
>
> * insert：新增模式
> * update：更新模式
>   - 根据DB_PRIMARY_KEY更新
>   - DB_UPDATE_EXCLUDE_FIELDS是排除不更新的值
>
> **MySQL需要先建表**
>
> id主键：字段类型要求32位字符

```python
'''
【存储】设置，DB_MODE提供新增（insert）和更新（update）两种模式，id为主键存储‘fingerprint’的值
'''
DB_MODE = 'insert'
DB_PRIMARY_KEY = ['id']
DB_UPDATE_EXCLUDE_FIELDS = ['id', 'create_time']
'''
【MySQL】设置，'mysql+asyncmy://用户名:密码@地址:端口/数据库?charset=utf8mb4&min_size=最小连接数&max_size=最大连接数'
'''
MYSQL_DB_URI = ''
MYSQL_TABLE_NAME = ''

'''
【MongoDB】设置，'mongodb://用户名:密码@地址:端口'
'''
MONGO_DB_URI = ''
MONGO_DB_NAME = ''
MONGO_COLLECTION_NAME = ''
```

#### 采集策略设置

> 代理IP：可以支持隧道代理，其他形式的代理需要自行实现
>
> 并发、延迟、超时都时经验值，需要结合业务确定
>
> 默认开启自动调频，不需要或开启异步可关闭

```python
'''
【代理IP】设置，格式：用户名:密码@地址:端口
'''
IP_PROXY_SERVICE = False
IP_PROXY_LIST = ['127.0.0.1:7890']

'''
【请求最大并发数】设置
'''
# CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 提高 Twisted IO 线程池大小
REACTOR_THREADPOOL_MAXSIZE = 16

'''
【下载延迟】设置
'''
DOWNLOAD_DELAY = 0.153

'''
【下载超时】设置，单位：秒
'''
DOWNLOAD_TIMEOUT = 28

'''
【下载重试】设置，RETRY_LOG、RETRY_LOG_404、RETRY_LOG_BAN记录三种不同日志，重点关注后俩，没有则不生成
'''
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 473]
RETRY_LOG = F"./debug/retry-log/{DEBUG_FILE_NAME}.txt"
RETRY_LOG_404 = F"./debug/retry-log/404/{DEBUG_FILE_NAME}.txt"
RETRY_LOG_BAN = F"./debug/retry-log/ban/{DEBUG_FILE_NAME}.txt"

'''
【自动调频功能开关、延迟初始值、调整幅度】设置，单位：秒
'''
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
# 开启自动调频的调试功能
AUTOTHROTTLE_DEBUG = True

'''
【通用爬虫策略】：定向爬虫需禁用
'''
# 禁用 Cookie
# COOKIES_ENABLED = False
# 深度优先级、调度策略
# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
# SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
# SCHEDULER_PRIORITY_QUEUE = 'scrapy.pqueues.DownloaderAwarePriorityQueue'
```

#### 伪装策略设置

> 其实，伪装的效果有限，一般网站随机UA+代理就可以了
>
> 遇到比较高端的网站还是需要破解逆向协议，遇到这种还是要自行实现代码
>
> 对于UA，建议还是使用相同平台的比较好，如PC的页面用PC的UA，若平台不一致，有可能出现返回手机端页面，对应的PC端字段解析也会失效

```python
'''
【随机User-Agent】设置
查看支持平台：https://github.com/ihandmine/anti-useragent/blob/main/doc/README_ZH.md#支持平台
'''
RANDOM_USER_AGENT = True
RANDOM_USER_AGENT_PLATFORM = ['windows', 'linux', 'mac']
RANDOM_USER_AGENT_BROWSER = ['chrome']
```

#### 中间件

> - DOWNLOADER_MIDDLEWARES
>   - 默认关闭`SeleniumCrawlMiddleware`：真正需要时在启用，如过5秒盾、加密强混淆、页面需要截图等
> - ITEM_PIPELINES
>   - 默认开启 MySQL 和 MongoDB 支持，不需要不用管
> - EXTENSIONS
>   - 默认关闭 TelnetConsole ，有需要可以在开启

#### 其他设置说明

> - 【调试】临时存储数据：FEEDS 不需要可以关闭
>
> - Asyncio：必须开启
>
>   ```python
>   '''
>   开启 Asyncio 支持
>   '''
>   if sys.platform == 'win32':
>       asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
>   ASYNCIO_EVENT_LOOP = "asyncio.SelectorEventLoop"
>   TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
>   ```
>
> - 【HTTP缓存】：默认关闭，若网站字段样例多需要反复修改，可以开启该设置
>
> - 【Scrapy-Redis】设置：若启用，最少需要设置`SCHEDULER`、`DUPEFILTER_CLASS`和`REDIS_URL`这三项



## Demo 2 列表页解析

> `ssr1_list.py` 是针对列表页解析的爬虫

### ssr1_list.py

```python
class Ssr1ListSpider(CrawlSpider):
    name = 'ssr1_list'
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
        create_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        update_time = datetime.now(tz=tz.gettz('Asia/Shanghai'))
        # parse_list来解析列表页字段
        return ScrapyTplpDemosItemLoader().parse_list(ResponseParser(response),
                                                      create_time=create_time,
                                                      update_time=update_time)
```

### items.py

```python
@classmethod
def parse_list(cls, response, **kwargs):
    group_list = response.selector.re(r'(<div class="el-card__body">[\D\d]*?</div>\s*</div>\s*</div>)\s*</d
    for group in group_list:
        item = ScrapyTplpDemosItem()
        # 用request_fingerprint计算url的指纹，作为主键
        # 但这个在同一页面提取多条数据的模式 url是一致，需要增加区别点一并计算主键，这里是 列表url+name+published_at
        name = re.search(r'<h2 [^>]*?class="m-b-sm">(.*?)</h2>', group).group(1)
        published_at_result = re.search(r'<div [^>]*?class="m-v-sm info">\s*<span.*?>(.*?) 上映</span>', grou
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
                                 re.search(r'<div [^>]*?class="m-v-sm info">([\D\d]*?)</span>', group).grou
                                     1)).split('、')
        item['minute'] = re.search(
            r'<div [^>]*?class="m-v-sm info">[\D\d]*?</span>[\D\d]*?</span>\s*<span[^>]*?>(\d+) 分钟</span>',
            group).group(1)
        item['published_at'] = published_at
        item['cover'] = re.search(r'<img[^>]*?src="([^>]*?)"\s*class="cover">', group).group(1)
        item['score'] = re.search(r'<p [^>]*?class="score m-t-md m-b-n-sm">\s*(\S*?)</p>', group).group(1)
        item['create_time'] = kwargs['create_time']
        item['update_time'] = kwargs['update_time']
        # 注意这里
        yield item
```

## Demo 3

> `spa2.py`是对于["https://spa2.scrape.center/"](https://spa2.scrape.center/)的爬虫，具体实现详见代码注释

#### spa2.py

```python
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
```

#### items.py

```python
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
```

