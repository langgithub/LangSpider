# coding:utf8
import time

from common import consts
from common.logger import logger
from influxdb import InfluxDBClient
from yamls import conf
from common.utils import logger_track


class InfluxdbHelper(object):
    """
    爬虫日志收集存储数据库
    """

    @logger_track
    def __init__(self):
        self.conf = conf
        _c = conf.influxdb_configs
        self.client = InfluxDBClient(_c['host'], _c['port'],
                                     _c['user'], _c['passwd'], _c['db_name'])
        self.__create_db(_c['db_name'])

    def __create_db(self, db_name):
        """
        创建数据库
        :param db_name: 数据库名称
        :return:
        """
        try:
            self.client.create_database(db_name)
        except Exception as e:
            logger.exception(e)

    def write_points(self, ps):
        """
        打点，插入数据库
        :param ps: 日志
        :return:
        """
        try:
            self.client.write_points(ps)
        except Exception as e:
            logger.exception(e)

    def record_phase(self, user_id, cell_phone, phase, province, merchant_id="",
                     status=consts.ST_CRAWL_SUCCESS,
                     msg="", t_diff=0):
        """
        日志收集字段
        :param token: 唯一标识
        :param phone: 手机号
        :param phase: 阶段
        :param status: 状态
        :param err_msg: 错误信息
        :param province: 省份必填
        :param t_diff:
        :return:
        """
        ps = []
        p = {
            'measurement': 'op_spider',
            "tags": {
                "merchant_id": merchant_id,
                "msg": msg,
                "phase": phase,
                "status": status,
                "province": province,
            },
            "fields": {
                "t_diff": t_diff,
                "user_id": user_id,
                "cell_phone": cell_phone,
            }
        }
        ps.append(p)
        self.write_points(ps)
