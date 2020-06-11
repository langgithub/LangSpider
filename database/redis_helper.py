# coding:utf8
import json
import pickle
from redis import ConnectionPool, StrictRedis
from common.consts import *
from yamls import conf
from common.utils import logger_track


class RedisHelper(object):
    """redis crud操作"""
    @logger_track
    def __init__(self):
        self.conf = conf
        self.url = self.conf.redis_configs['redis_url']
        self.pool = ConnectionPool.from_url(url=self.url)
        self.redis_cli = StrictRedis(connection_pool=self.pool, decode_responses=True)

    def get_info_by_token(self, key):
        """
        根据token获取info
        :param token:
        :return:
        """
        res = self.redis_cli.get(key)
        if not res:
            return FORBIDDEN
        res_ = json.loads(res)
        return res_

    def save_info_by_token(self, key, info):
        """
        存储info
        :param token:
        :param info:
        :return:
        """
        if not isinstance(info, dict):
            return TYPE_ERROR
        info_str = json.dumps(info)
        self.redis_cli.set(key, info_str, ex=60*60*3)
        return OK

    def get_phase(self, token):
        """
        根据token获取当前阶段
        :param token:
        :return:
        """
        res = self.redis_cli.get("yuyingshang:" + token)
        if not res:
            return FORBIDDEN
        res_ = json.loads(res)
        phase = res_.get("phase")
        if not phase:
            return NOT_FOUND
        return phase

    def update_phase(self, token, phase):
        """
        更新info中阶段
        :param token:
        :param phase:
        :return:
        """
        res = self.redis_cli.get(token)
        if not res:
            return FORBIDDEN
        res_ = json.loads(res)
        res_["phase"] = phase
        self.redis_cli.set(token, json.dumps(res_))
        return OK

    def saveCrawlResponse(self, key, crawlResponse):
        self.redis_cli.set(key, crawlResponse, ex=60 * 15)
        return OK

    def getObject(self, key):
        """
        获取类对象
        :param key:
        :return:
        """
        res = self.redis_cli.get(key)
        if not res:
            return None
        res_ = pickle.loads(res)
        return res_

    def saveOrUpdate(self, key, date, time=60*15):
        """
        存储redis
        :param key:
        :param date:
        :param time:  超时时间 秒
        :return:
        """
        self.redis_cli.set(key, date, ex=time)
        return OK

    def exists(self, key):
        return self.redis_cli.exists(key)

    def get(self, key):
        """
        获取json字符串
        :param key:
        :return:
        """
        res = self.redis_cli.get(key)
        if not res:
            return None
        res_ = json.loads(res)
        return res_

def run():
    pass


if __name__ == '__main__':
    run()
