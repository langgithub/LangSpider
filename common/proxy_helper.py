# coding:utf8
import json

import requests
from common.utils import check_env

environment = check_env()
if environment == "development":
    host = 'http://47.96.170.1:15003'
elif environment == "production":
    # host = 'http://10.10.4.3:15003'
    host = 'http://10.10.4.87:15003'
elif environment == "test":
    host = 'http://127.0.0.1:15003'
else:
    raise Exception("不正确的environment")
FAIL_SLEEP_TIME = 0
# host = 'http://47.96.170.1:15003'
# host = 'http://10.10.4.3:15003'
# host = 'http://127.0.0.1:15003'
token = '4cc5fbe69e2a93d48bef68319b763541'
TIMEOUT = 0.5


def get_proxy(isown, protocol, site, count=1, logger=None):
    try_times = 0
    while try_times < 2:
        try_times += 1
        try:
            url = '%s/select?isown=%s&protocol=%s&site=%s&token=%s&count=%s' % (
                host, isown, protocol, site, token, count)
            # print(url)
            res = requests.get(url, timeout=TIMEOUT)
            ps = json.loads(res.text)['data']
            # print("获取代理",ip)
            return ps
        except Exception as e:
            if logger:
                logger.error(str(e))
            else:
                print(str(e))
            # time.sleep(FAIL_SLEEP_TIME)
    return []


if __name__ == "__main__":
    print(get_proxy(isown=0, protocol=1, site='dianping', count=2))
