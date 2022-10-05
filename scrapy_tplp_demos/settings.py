import asyncio
import sys
import time

BOT_NAME = 'scrapy_tplp_demos'

SPIDER_MODULES = ['scrapy_tplp_demos.spiders']
NEWSPIDER_MODULE = 'scrapy_tplp_demos.spiders'

# robots.txt 协议（要严格遵守协议，控制好频率）
# ROBOTSTXT_OBEY = True

# 存储调试文件的文件名规则
DEBUG_FILE_NAME = time.time()
'''
【日志】设置：CRITICAL, ERROR, WARNING, INFO, DEBUG（默认）
'''
# LOG_LEVEL = 'INFO'
# LOG_FILE = F'scrapy_tplp_demos({time.strftime("%Y-%m-%d", time.localtime())}).log'
# LOG_STDOUT = True

'''
【调试】临时存储数据
'''
FEEDS = {
    F"./debug/data/{DEBUG_FILE_NAME}.txt": {"format": "jl"}
}

####################
#     监控报告      #
###################
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

####################
#     存储设置      #
###################
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

####################
#     采集策略      #
###################
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

####################
#     伪装策略      #
###################

'''
【User-Agent】设置 
若需要设置固定 USER_AGENT，设置 [RANDOM_USER_AGENT] 为 False
'''
# USER_AGENT = 'inspection_platform (+http://www.yourdomain.com)'

'''
【随机User-Agent】设置
查看支持平台：https://github.com/ihandmine/anti-useragent/blob/main/doc/README_ZH.md#支持平台
'''
RANDOM_USER_AGENT = True
RANDOM_USER_AGENT_PLATFORM = ['windows', 'linux', 'mac']
RANDOM_USER_AGENT_BROWSER = ['chrome']

'''
【通用请求头】设置
'''
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'DNT': 1
}

'''
【Ja3伪装】需关闭自动调频功能（AUTOTHROTTLE_ENABLED = False）
'''
DOWNLOADER_CLIENTCONTEXTFACTORY = 'anti_useragent.utils.scrapy_contextfactory.Ja3ScrapyClientContextFactory'

####################
#     中间件       #
###################

'''
【Spider】
See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
'''
SPIDER_MIDDLEWARES = {
    # 开启 爬虫异常监控 支持
    'scrapy_tplp_demos.components.middlewares.monitor.ExceptionSpiderMiddleware': 1,

    # 自定义 SPIDER_MIDDLEWARES
    # 'scrapy_tplp_demos.middlewares.ScrapyTplpDemosSpiderMiddleware': 543,
}

'''
【Downloader】
See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
'''
DOWNLOADER_MIDDLEWARES = {
    # 开启 中间件异常监控 支持
    'scrapy_tplp_demos.components.middlewares.monitor.ExceptionMiddleware': 1,
    # 开启 AiohttpRequest 支持
    'scrapy_tplp_demos.components.middlewares.aiohttpcrawl.AiohttpCrawlMiddleware': 585,
    # 开启 SeleniumRequest 支持
    # 'scrapy_tplp_demos.components.middlewares.seleniumcrawl.SeleniumCrawlMiddleware': 586,
    # 开启 随机UA 支持
    'scrapy_tplp_demos.components.middlewares.randomua.RandomUADownloadMiddleware': 499,
    # 开启 重试日志记录 支持
    'scrapy_tplp_demos.components.middlewares.retry.RetryLogMiddleware': 550,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    # 开启 代理IP 支持
    'scrapy_tplp_demos.components.middlewares.proxy.ProxyMiddleware': 749,

    # 自定义 DOWNLOADER_MIDDLEWARES
    # 'scrapy_tplp_demos.middlewares.ScrapyTplpDemosDownloaderMiddleware': 543,
}

'''
【Item Pipelines】
See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
'''
ITEM_PIPELINES = {
    # 开启 MYSQL 存储支持
    'scrapy_tplp_demos.components.pipelines.sql.SqlPipeline': 100,
    # 开启 MongoDB 存储支持
    'scrapy_tplp_demos.components.pipelines.nosql.MongoDBPipeline': 101,
    # 开启 文件 存储支持(Item 需要设置 path, filename, content, encoding 这四个字段)
    # 'scrapy_tplp_demos.components.pipelines.file.FilePipeline': 102,
    # Scrapy-Redis 是否存储到 redis
    # 'scrapy_redis.pipelines.RedisPipeline': 200,

    # 自定义 ITEM_PIPELINES
    # 'scrapy_tplp_demos.pipelines.ScrapyTplpDemosPipeline': 300,
}

'''
【Extensions】
See https://docs.scrapy.org/en/latest/topics/extensions.html
'''
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
    # 开启 推送报告 支持
    'scrapy_tplp_demos.components.extensions.report.Reporter': 1,
}

'''
【Download Handlers】
'''
# DOWNLOAD_HANDLERS = {
#     # 开启 HTTP2 支持
#     'https': 'scrapy.core.downloader.handlers.http2.H2DownloadHandler',
# }

'''
开启 Asyncio 支持
'''
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
ASYNCIO_EVENT_LOOP = "asyncio.SelectorEventLoop"
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

'''
【HTTP缓存】有助于重新结构化字段
See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
'''
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 86400 * 7
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_GZIP = True
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# 允许全部HTTP状态码
HTTPERROR_ALLOW_ALL = True

'''
【Scrapy-Redis】设置
See https://scrapy-redis.readthedocs.io/en/stable/
'''
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# Redis 连接设置
# REDIS_URL = 'redis://user:pass@hostname:port/db'
# Redis 持久化
# SCHEDULER_PERSIST = True
