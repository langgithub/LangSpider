#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/6/16 上午10:26
# file: sync_spider.py


import threading
import urllib3
from enum import Enum
from abc import abstractmethod
from lang_spider.common.logger import logger
from lang_spider.service.common_crawl import CommonCrawl
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


class SyncSpiderObj(Spider):
    """同步爬虫"""

    # 线程锁
    _instance_lock = threading.Lock()

    # 默认线程数
    __thread_num = 1

    def __init__(self, thread_num=1):
        self.__scheduler = QueueScheduler()
        self.__thread_num = thread_num
        self.__result = []

    def __new__(cls, *args, **kwargs):
        if not hasattr(SyncSpiderObj, "_instance"):
            with SyncSpiderObj._instance_lock:
                if not hasattr(Spider, "_instance"):
                    SyncSpiderObj._instance = super(SyncSpiderObj, cls).__new__(cls, *args, **kwargs)
        return SyncSpiderObj._instance

    def getResult(self):
        return self.__result

    @staticmethod
    def fetch(request: CommonCrawl):
        # 后期上中间件
        return request.crawl()

    def engine(self):
        # 阻塞方式获取任务
        while True:
            with ThreadPoolExecutor(max_workers=self.__thread_num) as t:
                all_task = []
                while not self.get_scheduler().empty() and self.get_status() == Status.RUNNING:
                    request = self.get_scheduler().get()
                    if request is None:
                        # 打印日志, 休息一会儿之类
                        logger.info("当前没有种子")
                    else:
                        task = t.submit(self.fetch, request)
                        all_task.append(task)

                # 异步获取返回结果，采用配置中间件来做后续操作,阻塞等待任务完成
                for future in as_completed(all_task):
                    data = future.result()
                    logger.debug(f"task result >>> {data}")
                    # 如果data is None 说明线程没有返回结果
                    if data is None:
                        raise Exception("thread func is no return")
                    else:
                        _data = data.to_dict()
                        self.__result.append(_data)
                logger.debug(self.__result)
                return

    def run(self):
        self.set_status(Status.RUNNING)
        self.engine()

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
