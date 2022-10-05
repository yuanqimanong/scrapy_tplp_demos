import random

from scrapy.exceptions import NotConfigured


class ProxyMiddleware:

    def __init__(self, ip_proxy_list):
        self.ip_proxy_list = ip_proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('IP_PROXY_SERVICE'):
            raise NotConfigured('请先启用配置文件中的【代理IP】设置！（IP_PROXY_SERVICE = True）')

        ip_proxy_list = set(str(x) for x in crawler.settings.get('IP_PROXY_LIST'))
        if len(ip_proxy_list) == 0:
            raise NotConfigured('您需要在配置文件的【IP_PROXY_LIST】中填写至少一个代理IP地址！')

        return cls(ip_proxy_list)

    def process_request(self, request, spider):
        proxy = random.choice(list(self.ip_proxy_list))
        if 'http' not in proxy:
            request.meta['proxy'] = F'http://{proxy}'
        else:
            request.meta['proxy'] = proxy
