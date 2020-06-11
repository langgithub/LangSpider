# encoding: utf-8
"""
@author: xsren 
@contact: bestrenxs@gmail.com
@site: xsren.me

@version: 1.0
@license: Apache Licence
@file: utils.py
@time: 17/11/2017 6:19 PM

"""
import re
import time
import math
import uuid
import json
import base64
import hashlib
import calendar
import bs4
import copy
import pyDes

from datetime import datetime
from Cryptodome.Cipher import AES

from flask_restplus import abort

from phone import Phone
from xpinyin import Pinyin
from common.logger import logger


def phone_check(phone):
    if phone:
        phone_pat = re.compile(r"^1[3-9]\d{9}$")
        res = re.search(phone_pat, phone)
        return res


def id_check(num_str, logger):
    num_str = num_str.lower()
    str_to_int = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
                  '6': 6, '7': 7, '8': 8, '9': 9, 'x': 10}
    check_dict = {0: '1', 1: '0', 2: 'x', 3: '9', 4: '8', 5: '7',
                  6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    if len(num_str) != 18:
        logger.error('请输入标准的第二代身份证号码')
        return False
    check_num = 0
    try:
        for index, num in enumerate(num_str):
            if index == 17:
                right_code = check_dict.get(check_num % 11)
                if num == right_code:
                    logger.debug(u"身份证号: %s 校验通过" % num_str)
                    return True
                else:
                    logger.error(u"身份证号: %s 校验不通过, 正确尾号应该为：%s" % (num_str, right_code))
                    return False
            check_num += str_to_int.get(num) * (2 ** (17 - index) % 11)
    except Exception as e:
        logger.error('身份证格式不正确')
        return False


def make_dict_from_orm_obj(obj):
    _dict = obj.__dict__
    _dict.pop('_sa_instance_state', None)
    for k, v in _dict.items():
        if isinstance(v, datetime):
            _dict[k] = datetime.strftime(v, "%Y-%m-%d %H:%M:%S")
    return _dict


def make_json_from_orm_obj(obj):
    if isinstance(obj, list):
        _json = []
        for o in obj:
            _dict = make_dict_from_orm_obj(o)
            _json.append(_dict)
        return _json
    else:
        _dict = make_dict_from_orm_obj(obj)
        return _dict


def remove_none_values_from_dict(_dict):
    # 先删除不能入库的数据
    _dict.pop('not_update', None)
    _dict.pop('TOKEN', None)
    return dict((k, v) for k, v in _dict.items() if v is not None)


def abort_if_account_doesnt_exist(db, aid):
    if not db.is_account_exist(aid):
        abort(401, message="账号 {} 不存在".format(aid))


def abort_if_account_server_doesnt_exist(db, as_name):
    if not db.is_account_server_exist(as_name):
        abort(401, message="Account Server {} 不存在".format(as_name))


def abort_if_user_doesnt_exist(db, username):
    if not db.is_user_exist(username):
        abort(401, message="用户 {} 不存在".format(username))


def check_env():
    """
    根据IP判断是本地环境还是线上环境
    :return:
    """
    import socket
    # 获取本机电脑名
    myname = socket.gethostname()
    # 获取本机ip
    try:
        myaddr = socket.gethostbyname(myname)
    except Exception as e:
        print(e)
        myaddr = '172.17'
    if "10.10.4" in myaddr:  # 本地
        return "production"
    else:
        return "development"


def check_phone_addr(phone: str):
    """
    检查手机的合法性和归属地
    :param phone:
    :return op:所属运营商  1 移动 yd  2 联通 lt 3 电信 dx 4 电信虚拟号 dxxnh 5 联通虚拟号 ltxxh 6 移动虚拟号 ydxnh
            pro:省份
    """
    consts = {"电信": "dx",
              "联通": "lt",
              "移动": "yd",
              "电信虚拟运营商": "dxxnh",
              "联通虚拟运营商": "ltxxh",
              "移动虚拟运营商": "ydxxh"}

    # TODO 检测手机号是否是字符串
    if not isinstance(phone, str):
        phone = str(phone)
    # 检查手机号合法性
    if phone_check(phone).group():
        gsd_ = Phone()
        pin = Pinyin()
        ret = gsd_.find(phone)
        op = consts.get(ret.get("phone_type"))
        ss = ret.get("province")
        # 替换规则
        if "陕西" in ss:
            pro = pin.get_pinyin("%s2" %ss, "").lower()
        elif "重" in ss:
            pro = pin.get_pinyin(ss, "").lower().replace("z", "c", 1)
        else:
            pro = pin.get_pinyin(ss, "").lower()
        # 当查找不到时通过百度查询
        if not pro or not op:
            op, pro = get_bd_phone_addr(phone)
        return op, pro


def check_phone_addr_2(phone: str):
    """
    检查手机的合法性和归属地
    :param phone:
    :return op:所属运营商  1 移动 yd  2 联通 lt 3 电信 dx 4 电信虚拟号 dxxnh 5 联通虚拟号 ltxxh 6 移动虚拟号 ydxnh
            pro:省份
            city:城市
    """
    consts = {"电信": "dx",
              "联通": "lt",
              "移动": "yd",
              "电信虚拟运营商": "dxxnh",
              "联通虚拟运营商": "ltxxh",
              "移动虚拟运营商": "ydxxh"}

    # TODO 检测手机号是否是字符串
    if not isinstance(phone, str):
        phone = str(phone)
    # 检查手机号合法性
    if phone_check(phone).group():
        gsd_ = Phone()
        pin = Pinyin()
        ret = gsd_.find(phone)
        op = consts.get(ret.get("phone_type"))
        city = ret.get('city')
        ss = ret.get("province")
        # 替换规则
        if "陕西" in ss:
            pro = pin.get_pinyin("%s2" % ss, "").lower()
        elif "重" in ss:
            pro = pin.get_pinyin(ss, "").lower().replace("z", "c", 1)
        else:
            pro = pin.get_pinyin(ss, "").lower()
        # 当查找不到时通过百度查询
        if not pro or not op:
            op, pro, city = get_bd_phone_addr2(phone)
        return op, pro, city


def get_bd_phone_addr(phone: str):
    """
    百度查询号码归属地
    :param phone: 手机号
    :return:
    """
    import requests
    url = "https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php"
    params = {
        "cb": "jQuery11020519188301599409_1545793214530",
        "resource_name": "guishudi",
        "query": str(phone),
        "_": "1545793214676"
    }
    ret = requests.get(url, params=params, timeout=2)
    json_ret = re.search(r"({.*})", ret.text)
    try:
        json_ret = json.loads(json_ret.group(0))
    except Exception as e:
        json_ret = {}
    if json_ret:
        op = json_ret.get("data")[0].get("type")
        pro = json_ret.get("data")[0].get("prov")
        return op, pro


def get_bd_phone_addr2(phone: str):
    """
    百度查询号码归属地
    :param phone: 手机号
    :return:返回运营商省份和城市
    """
    import requests
    url = "https://sp0.baidu.com/8aQDcjqpAAV3otqbppnN2DJv/api.php"
    params = {
        "cb": "jQuery11020519188301599409_1545793214530",
        "resource_name": "guishudi",
        "query": str(phone),
        "_": "1545793214676"
    }
    ret = requests.get(url, params=params, timeout=2)
    json_ret = re.search(r"({.*})", ret.text)
    try:
        json_ret = json.loads(json_ret.group(0))
    except Exception as e:
        json_ret = {}
    if json_ret:
        op = json_ret.get("data")[0].get("type")
        pro = json_ret.get("data")[0].get("prov")
        city = json_ret.get("data")[0].get("city")
        return op, pro, city

def create_token(name):
    import uuid
    namespace = uuid.NAMESPACE_URL
    return str(uuid.uuid3(namespace, str(name)))


def getuuid(s=""):
    """
    获取uuid
    :param s 分割线 默认以""分割
    """
    return f"{s}".join(str(uuid.uuid4()).split("-"))


def format_str(text):
    """
    格式化字符串
    text : str  传进来的必须是{xxx}形式
    """
    temp_str = ""
    text = re.sub("'", "\"", text)
    # 如果开头直接是"直接返回
    if text.startswith("{\"") or text.startswith("{}"):
        return text
    else:
        temp_list = text[1:-1].split(",")
        for i in temp_list:
            temp_i = i.split(":", 1)
            if not temp_i[0].startswith("\"") and not temp_i[0].endswith("\""):
                temp_str += "\"%s\"" % temp_i[0]
            else:
                temp_str += temp_i[0]
            if not temp_i[1].startswith("\"") and not temp_i[1].endswith("\""):
                temp_str += ":\"%s\"," % temp_i[1]
            else:
                temp_str += ":%s," % temp_i[1]
        else:
            temp_str = '{%s}' % temp_str[:-1]

    return temp_str


# 联通yaml读取配置用以后可以删除
def config(yaml_path, key: str = None):
    """
    传入yaml配置文件路径返回数据
    :param filepath: 配置文件路径
    :param key: 待取的配置信息 不传取全部配置   支持取子集   以  , 分割
    :return:
    """
    import yaml
    with open(yaml_path, encoding="utf-8") as f:
        conf = yaml.load(f.read(), Loader=yaml.Loader)
        if key and conf:
            if len(key.split(",")) == 1:
                return conf.get(key)
            else:
                temp = None
                for index, k in enumerate(key.split(",")):
                    if index == 0:
                        temp = conf.get(k)
                    else:
                        temp = temp.get(k)
                return temp
        else:
            return conf


def interface_time(func):
    """接口用时"""

    def wapper(*args, **kwargs):
        starttime = time.time()
        result = func(*args, **kwargs)
        endtime = time.time()
        print("[%s]接口用时：%ss" % (func.__name__, round(endtime - starttime, 2)))
        return result

    return wapper


def get_year_month(n=0, f="") -> tuple:
    """
    获取n个月前的年份和月份和天数
    :param n : n个月 当月算一个月 所以是往前5个月 算查询6个月数据  默认返回当月
    :param f : 分隔符
    :return yearx 年  monthx月 day_begin 当月第一天 day_end 当月过了几天 day_end 当月最后一天 date 当月为 哪年哪月
    """
    # 通用部分
    day_now = time.localtime()
    year = day_now.tm_year
    month = day_now.tm_mon  # 月份

    monthx = month - n
    yearx = year
    if monthx < 1:
        yearx = year - math.floor((12 + n) / 12)
        monthx = month + 12 - n

    day_begin = '%d%s%02d%s01' % (yearx, f, monthx, f)  # 月初肯定是1号
    # 联通部分使用
    wday, monthRange = calendar.monthrange(yearx, monthx)  # 得到本月的天数 第一返回为月第一日为星期几（0-6）, 第二返回为此月天数
    day_end = '%d%s%02d%s%02d' % (yearx, f, monthx, f, monthRange)
    # TODO 添加电信获取通话详单需要的参数值
    date = "%s%02d" % (yearx, monthx)
    if n != 0:
        return yearx, monthx, day_begin, day_end, day_end, date   # 第一个day_end 代表当月第几天， 第二个day_end 代表当月天数
    else:
        return yearx, monthx, day_begin, "%s%s%02d%s%02d" % (day_now.tm_year, f, day_now.tm_mon, f, day_now.tm_mday), \
               day_end, date


def get_now_date() -> str:
    """返回格式 YYYY-mm-dd HH:MM:SS"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# TODO 添加电信发送通话详单验证码 reDo参数
def get_redo_now_date() -> str:
    """移动发送通话详单验证码使用"""
    now = time.asctime(time.localtime(time.time())).split(" ")
    now[3], now[4] = now[4], now[3]
    return "%s GMT+0800 (中国标准时间)" % " ".join(now)  # 格式 Wed Jan 23 2019 09:57:18 GMT+0800 (中国标准时间)


def get_server_status(status: str):
    """获取电信用户服务状态"""
    if not status:
        return

    if "未知" in status:
        return "0"
    elif "正常" in status:
        return "1"
    elif "停机" == status:
        return "2"
    elif "单向停机" in status:
        return "3"
    elif "预销户" in status:
        return "4"
    elif "销" == status:
        return "5"
    elif "过户" in status:
        return "6"
    elif "改号" in status:
        return "7"
    elif "此号码不存在" in status:
        return "8"
    elif "挂失" in status or "冻结" in status:
        return "9"


class AESCipher(object):
    """aes 加密解密"""

    def __init__(self, key: str, iv: str) -> None:
        """
        初始化操作
        :param key:str 密钥
        :param iv:str 向量
        """
        temp_md5 = hashlib.md5()
        temp_md5.update(key.encode("utf-8"))
        self.key = temp_md5.hexdigest().encode("utf-8")
        self.iv = iv.encode()

    def pad(self, s: str) -> bytes:
        """补位
        :param s: 原始字符串
        return bytes 返回补位后的数据 并bytes形式返回
        """
        return (s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)).encode()

    def unpad(self, s: bytes) -> str:
        """
        去除补位数据
        :param s: 数据
        :return: 去除后的数据
        """
        return s[:-ord(s[len(s) - 1:])].decode('utf-8')

    def encrypt(self, raw: str) -> str:
        raw = self.pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        return base64.b64encode(cipher.encrypt(raw)).decode('utf-8')

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        return self.unpad(cipher.decrypt(enc))


def obj_to_dict(obj):
    """
    对象转dict，包含多对象嵌套
    :param obj:
    :return:
    """
    # int，float，bool，complex，str(字符串)，list，dict(字典)，set，tuple
    _to_dict = None

    def get_value(v):
        if isinstance(v, bool) or isinstance(v, str) or isinstance(v, float) or isinstance(v, int):
            return v
        elif v is None:
            return "None"
        elif isinstance(v, complex):
            return str(v)
        else:
            return obj_to_dict(v)

    if isinstance(obj, list) or isinstance(obj, set) or isinstance(obj, tuple):
        _to_dict = []
        for item in obj:
            _to_dict.append(get_value(item))
    elif isinstance(obj, dict):
        _to_dict = {}
        for k, v in obj.items():
            _to_dict[k] = get_value(v)
    else:
        _to_dict = {}
        for feild in obj.__dict__:
            _to_dict[feild] = get_value(obj.__dict__[feild])
    return _to_dict


def get_user_source(phone):
    """获取号码类型 示例值： DX_HEBEI"""
    op, pro = check_phone_addr(phone)
    return "%s_%s" % (op.upper(), pro.upper())


def md5(par):
    """
    md5加密
    :param par: 参数
    :return:
    """
    temp_md5 = hashlib.md5()
    if not type(par) is str:
        par = str(par)
    temp_md5.update(par.encode())
    return temp_md5.hexdigest()


def get_file(path):
    """
    加载file文件
    :param path:
    :return:
    """
    f = open(path, 'r', encoding='utf-8')  # 打开JS文件
    line = f.readline()
    htmlstr = ''
    while line:
        htmlstr = htmlstr + line
        line = f.readline()
    return htmlstr


def logger_track(func):
    def wrapper(self, *args, **kwargs):
        logger.debug(f"{self.__class__.__name__} 初始化开始")
        func(self, *args, **kwargs)
        logger.debug(f"{self.__class__.__name__} 初始化结束")

    return wrapper

def getCrawlerPageKey(user_id, merchant_id):
    """
    通过机构id和token获取redis key
    :param parent_id:  机构id
    :param token: 用户唯一标识
    :return: redsi key
    """
    return "crawlerpage_" + user_id + "_" + merchant_id

def getRedisKeyForParentIdAndPhone(merchant_id, user_id, cell_phone):
    """
    通过机构id,手机号,token获取redis key
    :param parent_id: 机构id
    :param phone: 手机号
    :param token: 用户唯一标识
    :return: reids key
    """
    return merchant_id + "_" + user_id + "_" + cell_phone

def warpData(operator, province, channel, fpath):
    """
    对存储的数据进行封装
    :param operator: 运营商
    :param province: 省份
    :param channel: 通道
    :param fpath: 路径
    :return: json.dumps
    """
    data = {"operator": operator, "province": province, "channel": channel, "fpath": fpath}
    return json.dumps(data)

def getParamData(sourceCode):
    """
    获取参数
    :param sourceCode:
    :return:
    """
    paramData = dict()
    doc = bs4.BeautifulSoup(sourceCode, "lxml")
    # 获取登陆需要的相关参数
    for ele in doc.select("input[type=hidden]"):
        if ele.get("name") != "" and ele.get("value") != None:
            paramData[ele.get("name")] = ele["value"]
        elif ele.get("id") != "" and ele.get("value") != None:
            paramData[ele.get("id")] = ele["value"]
    return paramData

def getMonthMap(monthCount, pattern=""):
    # 通用部分
    day_now = time.localtime()
    year = day_now.tm_year
    month = day_now.tm_mon  # 月份

    map = dict()
    for i in range(0, monthCount):
        monthx = month - i
        if monthx < 1:
            year = year - math.floor((12 + monthCount) / 12)
            monthx = month + 13 - monthCount
        day_begin = '%d%s%02d%s01' % (year, pattern, monthx, pattern)  # 月初肯定是1号
        # 联通部分使用
        wday, monthRange = calendar.monthrange(year, monthx)  # 得到本月的天数 第一返回为月第一日为星期几（0-6）, 第二返回为此月天数
        day_end = '%d%s%02d%s%02d' % (year, pattern, monthx, pattern, monthRange)
        date = "%s%02d" % (year, monthx)
        map[date] = (day_begin, day_end,)
    return map

def updateQuery(query, mobilePhoneQuery):
    """
    更新query
    :param query:
    :param mobilePhoneQuery:
    :return:
    """
    query.cell_phone = mobilePhoneQuery.cell_phone
    query.merchant_id = mobilePhoneQuery.merchant_id
    query.user_id = mobilePhoneQuery.user_id
    query.pic_code = mobilePhoneQuery.pic_code
    query.sms_code = mobilePhoneQuery.sms_code
    query.name = mobilePhoneQuery.name
    query.id_card = mobilePhoneQuery.id_card
    query.password = mobilePhoneQuery.pass_word
    return query

def getRedisKeyForProxy(query):
    """
    获取proxy key
    :param parent_id:  机构id
    :param token: 用户唯一标识
    :return: redsi key
    """
    return "proxy_" + query.merchant_id + "_" + query.user_id

def encrypt(key="", text=""):
    """
    DES ECB加密
    :param key:
    :param text:
    :return:
    """
    k = pyDes.triple_des(key, pyDes.ECB, IV=None, pad=None, padmode=pyDes.PAD_PKCS5)
    d = k.encrypt(text)
    res = base64.standard_b64encode(d)
    return res

if __name__ == '__main__':
    res = encrypt("kID3y56OqxH3mJToOAxfMOPq7XGapvv6","123456")
    print(res)