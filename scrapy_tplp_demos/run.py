#!/usr/bin/env python
# coding=utf-8

import multiprocessing
import os
import time

import psutil
from psutil import NoSuchProcess
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

next_time = None


def selenium_clear():
    time.sleep(3)
    pids = psutil.pids()
    for pid in pids:
        if psutil.Process(pid).name() == 'chromedriver.exe':
            try:
                os.system('taskkill /F /IM chromedriver.exe')
            except NoSuchProcess:
                pass
    time.sleep(2)
    user_data_dir = F'{os.path.abspath(r"..")}/components/selenium_cache/user_data_dir'
    try:
        if os.path.exists(user_data_dir):
            for root, dirs, files in os.walk(user_data_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
    except PermissionError:
        pass


def crawl_it(tasks_list):
    selenium_clear()
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    for task in tasks_list:
        process.crawl(task)
    process.start()


def do_tasks(tasks_list):
    process = multiprocessing.Process(target=crawl_it, args=(tasks_list,))
    process.start()
    print('任务开始运行！')
    process.join()
    if process.is_alive():
        process.terminate()
        print('任务停止运行！')
        process.join()
    print('任务运行结束！')
    selenium_clear()


if __name__ == '__main__':
    os.chdir('spiders')
    print("定时爬虫已启动！正在运行中...")

    # 爬虫任务名称列表，开启SeleniumRequest只能运行一个爬虫程序
    tasks_list = ['scrapy_tplp_demos', ]
    # 周期：分钟
    interval_minute = 15

    while True:
        next_time = time.time()
        do_tasks(tasks_list)
        end_time = time.time()
        if end_time - next_time < interval_minute * 60:
            time.sleep(interval_minute * 60 - end_time + next_time)
