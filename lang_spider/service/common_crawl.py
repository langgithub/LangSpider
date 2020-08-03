#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/8/3 上午10:50
# file: common_crawl.py


from abc import ABCMeta, abstractmethod


class CommonCrawl(metaclass=ABCMeta):

    @abstractmethod
    def crawl(self):
        pass
