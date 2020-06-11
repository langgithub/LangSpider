# encoding: utf-8
"""
--------------------------------------
@describe 爬虫基类，定义各种爬虫（运营商，微信，赌博）基本方法,与业务相关
@version: 1.0
@project: async_spider
@file: common_crawler.py
@author: yuanlang 
@time: 2019-01-11 16:27
---------------------------------------
"""
import os
import time
import wrapt
import requests

from database import ih
from model.fields import YysInfo
from common.logger import logger
from common.spider import Spider
from common import proxy_helper
from abc import ABCMeta, abstractmethod
from queue import Queue


def log_track(description=""):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        logger.info(f"爬虫 [{instance.__class__.__name__}.{wrapped.__name__}] description:{description}")
        result = wrapped(*args, **kwargs)
        try:
            if instance.info["result"]["res_code"] == 0:
                instance.info["status"] = instance.info["result"]["res_code"]
                instance.ih.record_phase(token=instance.token, phone=instance.phone, phase=instance.info["phase"],
                                         status=0, province=instance.info["channel"])
            else:
                instance.info["status"] = instance.info["result"]["res_code"]
                instance.ih.record_phase(token=instance.token, phone=instance.phone, phase=instance.info["phase"],
                                         status=1, province=instance.info["channel"],
                                         err_msg=instance.info["result"]["res_msg"])
        except Exception as e:
            pass
        return result

    return wrapper


class CommonCrawler(metaclass=ABCMeta):

    def __init__(self, token, info, img_path=os.path.dirname(os.path.dirname(__file__)) + "/img/",
                 spider=None, ih=ih):
        self.token = token
        self.info = info
        self.ih = ih
        self.phone = info["basic"]["phone"]
        self.pwd = info["basic"]["pwd"]
        self.sms_user = info["auth"]["jiao_hu"]["sms_user"]
        self.sms_bill = info["auth"]["jiao_hu"]["sms_bill"]
        self.img_user = info["auth"]["jiao_hu"]["img_user"]
        self.img_bill = info["auth"]["jiao_hu"]["img_bill"]
        self.spider = spider if spider else Spider(async_status=False)
        self.img_path = img_path
        self.ip_proxys = Queue()
        self.lock_ip = None
        self.ip_lock = []
        self.retry_count = 1
        self.test = False
        self.all_records = YysInfo()

    def update_cookie(self, cookie):
        requests.utils.add_dict_to_cookiejar(self.spider.requests.cookies, cookie)

    def get_cookies(self):
        return requests.utils.dict_from_cookiejar(self.spider.requests.cookies)

    def set_cookies(self, cookies):
        requests.utils.add_dict_to_cookiejar(self.spider.cookies,cookies)
        # self.spider.cookies = cookies
        requests.utils.add_dict_to_cookiejar(self.spider.requests.cookies, cookies)

    def delete_cookies(self):
        from requests.cookies import RequestsCookieJar
        self.spider.requests.cookies = RequestsCookieJar()

    def init_test(self):
        self.test = True

    def r_get(self, *args, **kwargs):
        """
        requests get请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.spider.r_get(get_proxy=self.reset_proxy, verify=False,proxies={"http":"http://127.0.0.1:8888"}, ip_proxy=True, crawler=self, *args, **kwargs)

    def r_post(self, *args, **kwargs):
        """
        requests post 请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.spider.r_post(get_proxy=self.reset_proxy, verify=False,proxies={"http":"http://127.0.0.1:8888"}, ip_proxy=True, crawler=self, *args, **kwargs)

    def a_get(self, *args, **kwargs):
        """
        async aiohttp get请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.spider.a_get(get_proxy=self.reset_proxy, ip_proxy=False, crawler=self, *args, **kwargs)

    def a_post(self, *args, **kwargs):
        """
        async aiohttp post请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.spider.a_post(get_proxy=self.reset_proxy, ip_proxy=False, crawler=self, *args, **kwargs)

    def save_byte(self, name, bs):
        """保存图片"""
        authcode_path = self.img_path
        suffix = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        path1 = authcode_path + suffix
        filename = path1 + "/" + name
        import os
        if not os.path.exists(path1):
            os.makedirs(path1)
        with open(filename, "wb") as f:
            f.write(bs)
        return filename

    def reset_proxy(self, method="get", proxy=None, delete=True):
        if method == "get":
            if self.lock_ip is not None:
                return self.lock_ip
            if self.ip_proxys.empty():
                proxys = proxy_helper.get_proxy(isown=2, protocol=1, site='dianping', count=1)
                for proxy in proxys:
                    key = f'http://{proxy["ip"]}:{proxy["port"]}'
                    # value = aiohttp.BasicAuth(proxy["uname"], proxy["passwd"])
                    self.ip_proxys.put(key)
            self.lock_ip = self.ip_proxys.get()
            logger.debug(f"获取代理 {self.lock_ip}")
            return self.lock_ip
        elif method == "update":
            if proxy is None:
                return
            if not delete:
                self.ip_proxys.put(proxy)
            else:
                logger.debug(f"移除无效的IP: {proxy}")
                self.lock_ip = None

    @abstractmethod
    def check_verify_code(self):
        """
        登陆 验证码刷新前操作
        :return:
        """
        pass

    @abstractmethod
    def refresh_img_user(self):
        """
        登陆 刷新图片验证码
        :return:
        """
        pass

    @abstractmethod
    def refresh_img_user_check(self):
        """
        登陆 验证图片验证码
        :return:
        """
        pass

    @abstractmethod
    def refresh_sms_user(self):
        """
        登陆 刷新短信验证码
        :return:
        """
        pass

    @abstractmethod
    def login_user(self):
        """用户登陆"""
        pass

    @abstractmethod
    def refresh_img_bill(self):
        """
        详单抓取 刷新图片验证码
        :return:
        """
        pass

    @abstractmethod
    def refresh_img_bill_check(self):
        """
        详单抓取 验证图片验证码
        :return:
        """
        pass

    @abstractmethod
    def refresh_sms_bill(self):
        """
        详单抓取 刷新短信验证码
        :return:
        """
        pass

    @abstractmethod
    def login_bill(self):
        """详单抓取登陆"""
        pass

    def crawl_addr_list(self):
        """抓取通话详单"""
        self.get_details()
        self.get_user_info()

    @abstractmethod
    def get_details(self):
        """获取详细信息"""
        pass

    @abstractmethod
    def get_user_info(self):
        """获取用户信息"""
        pass

    def set_status(self, _status):
        self.spider.set_status(_status)

    def stop(self):
        self.spider.stop()

    def run(self):
        # redis中取出cookie
        # self.spider.cookies = self.info["auth"]["cookies"]
        self.spider.run()
        # spider中的cookie 更新到redis
        # self.spider.cookies
        # 保存infoß
        # rh.save_info_by_token(self.token, self.info)
