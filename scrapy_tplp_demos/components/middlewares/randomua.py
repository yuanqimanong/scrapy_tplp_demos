import random

from anti_useragent import UserAgent
from scrapy.exceptions import NotConfigured


class RandomUADownloadMiddleware:

    def __init__(self, random_user_agent_platform, random_user_agent_browser):
        self.random_user_agent_platform = random_user_agent_platform
        self.random_user_agent_browser = random_user_agent_browser

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('RANDOM_USER_AGENT'):
            raise NotConfigured('请先启用配置文件中的【随机UserAgent】设置！（RANDOM_USER_AGENT = True）')
        random_user_agent_platform = list(
            str(x) for x in crawler.settings.get('RANDOM_USER_AGENT_PLATFORM') or ['windows', 'linux', 'mac'])
        random_user_agent_browser = list(
            str(x) for x in crawler.settings.get('RANDOM_USER_AGENT_BROWSER') or ['chrome'])
        return cls(random_user_agent_platform, random_user_agent_browser)

    @property
    def random_user_agent(self):
        ua = UserAgent(platform=random.choice(self.random_user_agent_platform))
        browser = random.choice(self.random_user_agent_browser)
        return getattr(ua, browser)

    def process_request(self, request, spider):
        request.headers.setdefault(b'User-Agent', self.random_user_agent)
