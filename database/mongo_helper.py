# coding:utf8

from common.consts import *
from pymongo import MongoClient
from yamls import conf
from common.utils import logger_track


class MongoHelper(object):
    """
    mongodb 数据crud
    """
    @logger_track
    def __init__(self):
        self.conf = conf
        self.db_conf = self.conf.db_configs
        self.mc = MongoClient(self.db_conf['host'], self.db_conf['port'], maxPoolSize=10)
        self.db = self.conn()

    def conn(self):
        """
        建立连接
        :return:
        """
        if self.db_conf['type'] == 'mongo':
            if self.db_conf.get('user') or self.db_conf.get('passwd'):
                self.mc[self.db_conf['db_name']].authenticate(self.db_conf['user'], self.db_conf['passwd'])
            db = self.mc[self.db_conf['db_name']]
            print('db......')
            return db
        else:
            raise Exception("不支持的db类型：{}".format(self.db_conf['type']))

    def save_data(self, token, phone, _data):
        """
        存储抓取的数据
        :param token:
        :param phone:
        :param _data:
        :return:
        """
        if self.db[self.db_conf['detail_data']].find_one({"token": token, "phone": phone}):
            return
        self.db[self.db_conf['detail_data']].insert_one(_data)
        return OK

    def check_partner_id(self, partner_id):
        """
        验证合作商是否存在
        :param partner_id: 合作商id
        :return:
        """
        if self.db[self.db_conf['partner']].find_one({"partner_id": partner_id}):
            return True
        else:
            return False

    def get_channel(self, op, pro):
        """
        获取运营商通道, web app m wap
        :param op: 运营商类别
        :param pro: 运营商省份
        :return:
        """
        result = self.db[self.db_conf['channel']].find_one({"operator": op, "province": pro, "terminal": "shop"})
        if result:
            return result['operator'] + "_" + result['province'] + "_shop", result['fpath'], result['extractPath']
        else:
            return None, None, None

    # TODO 获取规则表
    def get_login_rule(self, channel):
        """
        获取运营商登陆规则信息
        :param channel 管道
        :return:
        """
        result = self.db[self.db_conf['login_rule']].find_one({"channel": channel})
        return result.get("rule")

    def get_bill_rule(self, channel):
        """
        获取运营商详单规则信息
        :param channel 管道
        :return:
        """
        result = self.db[self.db_conf['bill_rule']].find_one({"channel": channel})
        return result.get("rule")

    def insert(self, _data):
        """
        插入一条通道数据
        :param _data:
        :return:
        """
        self.db[self.db_conf['channel']].insert_one(_data)

    def insert_login_rule(self, _data):
        """
        插入一条规则
        :param _data:
        :return:
        """
        self.db[self.db_conf['login_rule']].insert_one(_data)

    def insert_bill_rule(self, _data):
        """
        插入一条规则
        :param _data:
        :return:
        """
        self.db[self.db_conf['bill_rule']].insert_one(_data)


if __name__ == "__main__":
    mh = MongoHelper()
    data = {
        "channel_rule": "本地",
        "province": "sichuan",
        "operator": "yd",
        "terminal": "商城",
        "fpath": "spiders.lt.web.async_spider.LtSpider"
    }

    mh.insert(_data=data)
