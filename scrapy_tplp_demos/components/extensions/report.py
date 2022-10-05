from datetime import timedelta

from scrapy import signals

from scrapy_tplp_demos.components.utils.dingding import DingDingRobot


class Reporter:

    def __init__(self, settings, stats):
        self.stats = stats
        monitor_dingding_web_hook = settings.get('MONITOR_DINGDING_WEB_HOOK') or ''
        monitor_dingding_secret = settings.get('MONITOR_DINGDING_SECRET') or ''
        monitor_dingding_at_mobiles = list(
            str(x) for x in settings.get('MONITOR_DINGDING_AT_MOBILES') or [])

        report_dingding_web_hook = settings.get('REPORT_DINGDING_WEB_HOOK') or ''
        report_dingding_secret = settings.get('REPORT_DINGDING_SECRET') or ''
        report_dingding_at_mobiles = list(
            str(x) for x in settings.get('REPORT_DINGDING_AT_MOBILES') or [])

        self.ding_talk = None
        if '' != report_dingding_web_hook and '' != report_dingding_secret:
            self.ding_talk = DingDingRobot(report_dingding_web_hook, report_dingding_secret)
            self.report_dingding_at_mobiles = report_dingding_at_mobiles
        elif '' != monitor_dingding_web_hook and '' != monitor_dingding_secret:
            self.ding_talk = DingDingRobot(monitor_dingding_web_hook, monitor_dingding_secret)
            if len(report_dingding_at_mobiles) != 0:
                self.report_dingding_at_mobiles = report_dingding_at_mobiles
            elif len(monitor_dingding_at_mobiles) != 0:
                self.report_dingding_at_mobiles = monitor_dingding_at_mobiles

    @classmethod
    def from_crawler(cls, crawler):
        o = cls(crawler.settings, crawler.stats)
        crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
        return o

    def spider_closed(self, spider):
        task_name = spider.name
        if hasattr(spider, 'system_name'):
            task_name = spider.system_name

        stats = self.stats.get_stats()
        # print(pprint.pformat(stats))
        start_time = (stats.get('start_time') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        finish_time = (stats.get('finish_time') + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        elapsed_time_minute = round(stats.get('elapsed_time_seconds') / 60, 2)

        request_count = stats.get('downloader/request_count') or 0
        request_bytes = stats.get('downloader/request_bytes') or 0
        response_count = stats.get('downloader/response_count') or 0
        response_bytes = stats.get('downloader/response_bytes') or 0

        item_scraped_count = stats.get('item_scraped_count') or 0

        msg = F'''【{task_name}】抓取报告
程序运行时间：约{elapsed_time_minute}分钟（{start_time} ~ {finish_time}）
发送了 {request_count} 个请求（流量 {request_bytes} 字节）
接收到 {response_count} 个响应（流量 {response_bytes} 字节）
采集入库数据量：{item_scraped_count} 条记录
'''

        # msg = pprint.pformat(stats)
        if self.ding_talk:
            self.ding_talk.send_msg(msg, self.report_dingding_at_mobiles)
