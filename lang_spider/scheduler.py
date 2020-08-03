#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author：yuanlang
# creat_time: 2020/7/16 上午10:34
# file: scheduler.py

import json
from lang_spider.common import utils
from abc import ABCMeta, abstractmethod
from queue import Queue
# from database import kh


class Scheduler(metaclass=ABCMeta):
    queue = None  # 容器

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def put(self, task):
        pass

    @abstractmethod
    def empty(self):
        pass


class QueueScheduler(Scheduler):

    def __init__(self):
        self.queue = Queue()

    def get(self):
        try:
            return self.queue.get(block=False)
        except Exception as e:
            print(e)
            return None

    def put(self, seed):
        self.queue.put(seed)

    def empty(self):
        flag = False
        try:
            flag = self.queue.empty()
        except Exception as e:
            print(e)
        return flag


class KafkaScheduler(Scheduler):

    def __init__(self):
        self.queue = Queue()

    def get(self):
        return kh.get_task_by_anysc()

    def put(self, seed):
        request_str=kh.put_task(utils.obj_to_dict(seed))
        request_dict=json.loads(request_str)


    def empty(self):
        return True
