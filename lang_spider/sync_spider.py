#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/6/16 上午10:26
# file: sync_spider.py

import time
import requests
import threading
import urllib3
from enum import Enum
from abc import abstractmethod
from lang_spider.logger import logger
from lang_spider.web_http import Request,Response
from lang_spider.scheduler import QueueScheduler
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings()


class Status(Enum):
    """控制机器运行状态"""
    RUNNING = 0
    PAUSED = 1
    STOPPED = 2


class Spider(object):
    """一个抽象的爬虫，提供最基础的服务"""

    # 默认爬虫调度器
    __scheduler = None
    # middleware 后期扩展中间件
    __middleware = None
    # 爬虫状态
    __status = Status.STOPPED

    @abstractmethod
    def engine(self):
        """
        爬虫核心
        1. 包含启动引擎
        2. 分发工作
        3. 数据处理
        :return:
        """
        pass

    @abstractmethod
    def run(self):
        """爬虫启动"""
        pass

    @abstractmethod
    def pause(self):
        """爬虫暂停"""
        pass

    @abstractmethod
    def stop(self):
        """爬虫结束"""
        pass

    def get_status(self):
        return self.__status

    def set_status(self, status):
        self.__status = status


class SyncSpider(Spider):
    """同步爬虫"""

    # 线程锁
    _instance_lock = threading.Lock()

    # 默认线程数
    __thread_num = 1

    def __init__(self, thread_num=1):
        self.__scheduler = QueueScheduler()
        self.__thread_num = thread_num
        self.__session = requests.session()

    @property
    def session(self):
        return self.__session

    def __new__(cls, *args, **kwargs):
        if not hasattr(SyncSpider, "_instance"):
            with SyncSpider._instance_lock:
                if not hasattr(Spider, "_instance"):
                    SyncSpider._instance = super(SyncSpider, cls).__new__(cls, *args, **kwargs)
        return SyncSpider._instance

    def fetch(self, request: Request):
        # 后期上中间件
        while True:
            request.proxies = self.get_proxy()
            try:
                logger.debug("fetch url >>> {}".format(request.url))
                response = self.__session.request(url=request.url, method=request.method, params=request.params, data=request.data, headers=request.headers,
                                              cookies=request.cookies, files=request.files, auth=request.auth, timeout=request.timeout,
                                              allow_redirects=request.allow_redirects, proxies=request.proxies, hooks=request.hooks,
                                              stream=request.stream, verify=False, cert=request.cert, json=request.json)

                my_response = Response()
                if request.encoding is not None: response.encoding = request.encoding
                my_response.url = response.url
                my_response.text = response.text
                my_response.content = response.content
                my_response.headers = response.headers
                my_response.cookies = response.cookies
                my_response.meta = request.meta
                my_response.status_code = response.status_code
                if response.status_code == 200:
                    if request.callback is not None:
                        return request.callback(my_response)
                    else:
                        return self.parse(my_response)
                else:
                    logger.debug("code is {0} 重跑".format(response.status_code))
                    logger.debug(response.text)
            except Exception as e:
                logger.error(str(e))
                if "proxy" in str(e):
                    continue
                else:
                    logger.exception(e)
                    raise Exception(str(e))

    def engine(self):
        # 多少次没有获取任务就停止爬虫
        stop_count = 100
        has_task = False
        all_task = []
        with ThreadPoolExecutor(max_workers=self.__thread_num) as t:
            while self.get_status() == Status.RUNNING:
                # 每次抓取1000下，保存结果。限流
                for i in range(1000):
                    if not self.get_scheduler().empty():
                        seed = self.get_scheduler().get()
                        task = t.submit(self.fetch, seed)
                        all_task.append(task)
                        has_task = True
                    else:
                        # logger.debug("休息2s")
                        time.sleep(2)
                        if not has_task:
                            stop_count = stop_count - 1
                        else:
                            stop_count = 100
                        # 连续10次长时间没有任务，代表任务已经完成
                        if stop_count < 1:
                            self.set_status(Status.STOPPED)
                            break
                        has_task = False

    def run(self):
        self.start_request()
        self.set_status(Status.RUNNING)
        t = threading.Thread(target=self.engine)
        t.start()

    def pause(self):
        self.set_status(Status.PAUSED)

    def stop(self):
        self.set_status(Status.STOPPED)

    def set_scheduler(self, scheduler):
        """
        设置调度器
        :param scheduler:
        :return:
        """
        # 获取scheduler 的类型是否是scheduler类型
        # if scheduler is None:
        self.__scheduler = scheduler
        return self

    def add_request(self, request):
        """
        添加种子到调度器
        :param request:
        :return:
        """
        self.__scheduler.put(request)
        return self

    def get_scheduler(self):
        return self.__scheduler

    @abstractmethod
    def start_request(self):
        pass

    @abstractmethod
    def parse(self, response: requests.Response):
        pass

    @staticmethod
    def get_proxy():
        return None
