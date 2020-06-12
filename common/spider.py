# encoding: utf-8
"""
--------------------------------------
@describe 
@version: 1.0
@project: async_spider
@file: spiders.py
@author: yuanlang
@time: 2019-01-11 16:26
---------------------------------------
"""
import time
import asyncio
import aiohttp
import requests
import urllib3

from common.logger import logger
from common.web_http import Request, Response, get_cookie_from_headers, update_cookie_to_headers
from common.scheduler import QueueScheduler
from common.utils import obj_to_dict
from requests.cookies import RequestsCookieJar

urllib3.disable_warnings()


def http_aop(func):
    def wrapper(self, url, headers=None, callback=None, ip_proxy=True, proxies=None, timeout=5,
                meta=None, get_proxy=None, description=None, crawler=None, *args, **kwargs):
        """
        requests get请求
        :param description:
        :param get_proxy:
        :param meta: 额外参数
        :param url:
        :param timeout: 超时默认5s
        :param proxies: 代理，自己穿过来的 proxies={"http":"http://127.0.0.1:8888"}
        :param ip_proxy: 是否开启自动开启代理，默认开启
        :param self:
        :param headers: 请求头
        :param callback: 回调函数
        :param crawler: 爬虫对象
        :param args:
        :param kwargs:
        :return:
        """

        # 全局爬虫状态控制
        if not self.status:
            return

        # 后期可配置user——aget 池
        User_Agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/71.0.3578.98 Safari/537.36"
        if headers is None:
            headers = {
                "User-Agent": User_Agent
            }
        else:
            if headers.get("User-Agent", "") == "":
                headers["User-Agent"] = User_Agent

        # 代理装载配置
        proxy = None
        _proxies = proxies
        if ip_proxy and proxies is None and get_proxy is not None:
            proxy = get_proxy()
            proxies = {"http": proxy}

        try:
            # 爬虫日志信息记录
            if description is not None:
                logger.info(f"fetch: {url} [{description}] ")
            else:
                logger.info(f"fetch: {url}")

            # logger debug日志
            requests.utils.add_dict_to_cookiejar(self.requests.cookies, get_cookie_from_headers(headers))
            # logger.debug(f'request请求前： cookie {requests.utils.dict_from_cookiejar(self.requests.cookies)}')
            # 访问网络
            reponse = func(self, url=url, headers=headers, timeout=timeout, proxies=proxies, *args, **kwargs)
            if reponse.status_code != 200 and reponse.status_code != 302 and reponse.status_code != 301:
                logger.warn(f"异常代码号>>>>>>>>>>>>>>>>>>>>>> {reponse.status_code}，请检查")
                logger.warn("中断后续爬虫，爬虫已停止")
                self.set_status(False)
            # TODO 同步cookies到aiohttp
            requests.utils.add_dict_to_cookiejar(self.cookies, reponse.cookies.get_dict() if reponse.cookies else {})
            # logger debug日志
            # logger.debug(f'reponse返回后： cookie {requests.utils.dict_from_cookiejar(self.requests.cookies)}')
            # # 释放代理IP
            # get_proxy(method="update", proxy=proxy, delete=False)
            # 执行回调解析
            if callback is not None:
                if meta is not None:
                    reponse.meta = meta
                    callback(reponse)
                else:
                    callback(reponse)
        except Exception as e:
            # 开启重试，重试多少次失败
            logger.error(f"{repr(e)} fetch: {url} {meta}")
            # 代理错误，连接错误，和连接超时错误重试机制
            if "Proxy" in str(repr(e)) or "Timeout" in str(repr(e)):
                if ip_proxy and proxy is not None:
                    get_proxy(method="update", proxy=proxy, delete=True)
                if self.retry < 5:
                    self.retry = self.retry + 1
                    logger.debug(f"先休息0.5s,重试第{self.retry}次 url:{url}")
                    time.sleep(.5)
                    self.r_get(url=url, headers=headers, callback=callback, ip_proxy=ip_proxy, get_proxy=get_proxy,
                               proxies=_proxies, meta=meta, timeout=timeout, description=description,
                               crawler=crawler, *args, **kwargs)

                else:
                    self.set_status(False)
                    # TODO 优化爬虫引擎 超时请求直接返回不触发 callback
                    logger.error("用户 %s 请求【%s】超时" % (crawler.phone, url))
                    # crawler.info["result"] = obj_to_dict(Result(res_code=1, res_msg="请求超时"))

            # 其他错误异常中断
            else:
                self.set_status(False)
                logger.error("中断后续爬虫，爬虫已停止")

    return wrapper


from abc import ABCMeta, abstractmethod
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

class Status(Enum):
    """控制机器运行状态"""
    RUNNING = 0
    PAUSED = 1
    STOPPED = 2



class Spider(object):
    """一个抽象的爬虫，提供最基础的服务"""

    # 爬虫调度器
    __scheduler = None
    # middleware 后期扩展中间件
    __middleware = None
    # 爬虫状态
    __status = Status.STOPPED

    def __init__(self, scheduler):
        self.__schedule = scheduler

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

    def add_seed(self, request):
        """
        添加种子到调度器
        :param request:
        :return:
        """
        self.__scheduler.put(request)
        return self

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    def get_status(self):
        return self.__status

    # @status.setter
    # def status(self, status):
    #     self.__status = status

    def get_scheduler(self):
        return self.__scheduler


class SyncSpider(Spider):

    def __init__(self, scheduler=QueueScheduler()):
        super(SyncSpider, self).__init__(scheduler)
        self.__session = requests.session()
        # 默认线程数
        self.__thread_num = 5

    def fetch(self, request):
        pass

    def engine(self):
        # 阻塞方式获取任务
        while True:
            with ThreadPoolExecutor(max_workers=self.__thread_num) as t:
                all_task=[]
                while not self.get_scheduler().empty() and self.get_status() == Status.RUNNING:
                    request = self.get_scheduler().get()
                    if request is None:
                        # 打印日志, 休息一会儿之类
                        logger.info("当前没有种子")
                    else:
                        task = t.submit(self.fetch, request)




    def run(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass


class AsyncSpider(Spider):

    def __init__(self, scheduler=QueueScheduler()):
        super(AsyncSpider, self).__init__(scheduler)
        self.loop = asyncio.new_event_loop()
        # cookie池
        self.__cookies = RequestsCookieJar()
        self.retry = 1
        self.__sleep_time = 0
        self.status = True

    def set_status(self, value):
        self.status = value

    @property
    def sleep_time(self):
        return self.__sleep_time

    @sleep_time.setter
    def sleep_time(self, time):
        self.__sleep_time = time

    @http_aop
    def r_get(self, *args, **kwargs):
        """
        requests get请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.requests.get(*args, **kwargs)

    @http_aop
    def r_post(self, *args, **kwargs):
        """
        requests post 请求
        :param args:
        :param kwargs:
        :return:
        """
        return self.requests.post(*args, **kwargs)

    def a_get(self, *args, **kwargs):
        """
        async aiohttp get请求
        :param args:
        :param kwargs:
        :return:
        """
        request = Request(method="GET", *args, **kwargs)
        self.add_request(request)

    def a_post(self, *args, **kwargs):
        """
        async aiohttp post请求
        :param args:
        :param kwargs:
        :return:
        """
        request = Request(method="POST", *args, **kwargs)
        self.add_request(request)

    def add_request(self, request):
        self.scheduler.put(request)

    async def fetch(self, session, request: Request):
        if request.description is not None:
            logger.info(f"fetch: {request.url} [{request.description}] ")
        else:
            logger.info(f"fetch: {request.url}")
        proxy = request.proxies
        try:
            requests.utils.add_dict_to_cookiejar(self.cookies, request.cookies if request.cookies else {})
            # self.cookies.update(request.cookies if request.cookies else {})
            update_cookie_to_headers(request.headers, requests.utils.dict_from_cookiejar(self.cookies))
            # logger.debug(f'request请求前： cookie {self.cookies}')

            if request.ip_proxy and request.get_proxy is not None and proxy is None:
                request.proxies = request.get_proxy()
            async with session.request(method=request.method, url=request.url, params=request.params, data=request.data,
                                       json=request.json, headers=request.headers, timeout=request.timeout,
                                       proxy=request.proxies, verify_ssl=False) as resp:
                response = Response()
                response.content = await resp.read()
                response.text = response.content.decode(encoding=request.encoding)
                response.status_code = resp.status
                response.url = resp.url.__str__()
                response.set_cookie_from_aiohttp(resp.cookies)
                response.headers = resp.headers
                response.meta = request.meta
                # self.cookies.update(requests.utils.dict_from_cookiejar(response.cookies))
                requests.utils.add_dict_to_cookiejar(self.cookies, requests.utils.dict_from_cookiejar(response.cookies))
                # logger.debug(f'reponse返回后： cookie {self.cookies}')
                # request.get_proxy(method="update", proxy=request.proxies, delete=False)
                if response.status_code != 200 and response.status_code != 302:
                    logger.warn(f"异常代码号>>>>>>>>>>>>>>>>>>>>>> {response.status_code}，请检查")
                    logger.warn("中断后续爬虫，爬虫已停止")
                    self.set_status(False)
                return request.callback, response
        except Exception as e:
            # 开启重试，重试多少次失败
            logger.error(f"{repr(e)} fetch: {request.__dict__}")
            # 代理错误，和连接超时错误重试机制
            if "Proxy" in str(repr(e)) or "Timeout" in str(repr(e)) or "Cannot connect to host" in str(repr(e)):
                if request.ip_proxy and proxy is None:
                    request.get_proxy(method="update", proxy=request.proxies, delete=True)
                    request.proxies = proxy
                if request.retry < 5:
                    request.retry = request.retry + 1
                    self.add_request(request)
                    logger.debug(f"重试第{request.retry}次 url:{request.url}")
                else:
                    # TODO 优化爬虫引擎 超时请求直接返回不触发 callback
                    logger.error("用户 %s 请求【%s】超时" % (request.crawler.phone, request.url))
                    # request.crawler.info["result"] = obj_to_dict(Result(res_code=1, res_msg="请求超时"))
                    return None, None

            return None, None

    async def engine(self):
        # async with aiohttp.connector.TCPConnector(limit=300) as tc: 限制连接
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            tasks = []
            while not self.scheduler.empty() or self.async_status:
                while not self.scheduler.empty() or self.async_status:
                    # 限流
                    # with asyncio.Semaphore(5):
                    request = self.scheduler.get()
                    if request is None:
                        break
                    task = asyncio.ensure_future(self.fetch(session=session, request=request))

                    def callback(done_task: asyncio.Task):
                        if done_task.done():
                            request_callback, response = done_task.result()
                            if request_callback is not None:
                                request_callback(response)

                    task.add_done_callback(callback)
                    tasks.append(task)
                    await asyncio.sleep(self.__sleep_time)

                # await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.gather(*tasks)
                if self.async_status: logger.debug("当前任务已经处理完成，等待下一批...")
                await asyncio.sleep(3)
            if self.async_status: logger.debug("任务已处理完成，队列没有任务了，爬虫即将退出")

    def run(self):
        logger.debug("spiders is start！！！")
        self.loop.run_until_complete(self.engine())
        logger.debug("spiders is stop！！！")

    def async_status(self):
        self.async_status = False

    def stop(self):
        pass
