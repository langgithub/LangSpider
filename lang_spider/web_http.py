#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author：yuanlang
# creat_time: 2020/7/16 上午10:34
# file: web_http.py

import re
import time
from requests.cookies import RequestsCookieJar
from http.cookiejar import Cookie


class Request(object):

    def __init__(self, url, method, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                 timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                 json=None, callback=None, meta=None, encoding=None):
        self.url = url
        self.method = method
        self.params = params
        self.data = data
        self.headers = headers
        self.cookies = cookies
        self.files = files
        self.auth = auth
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.proxies = proxies
        self.hooks = hooks
        self.stream = stream
        self.verify = verify
        self.cert = cert
        self.json = json
        self.callback = callback
        self.meta = meta
        self.encoding =encoding


class Response(object):

    def __init__(self, content=None, text=None, status_code=None, url=None, meta=None, cookies=RequestsCookieJar(),
                 headers=None):
        self.content = content
        self.text = text
        self.status_code = status_code
        self.url = url
        self.cookies = cookies
        self.headers = headers
        self.meta = meta

    def set_cookie_from_aiohttp(self, cookies):
        for k, v in cookies.items():
            expires = "0"
            if v["expires"] != "":
                if "-" in v["expires"]:
                    regex = re.compile(".*-.*-\d{4} .*")
                    if len(regex.findall(v["expires"])) != 0:
                        gmt_pormat = '%a, %d-%b-%Y %H:%M:%S GMT'
                    else:
                        gmt_pormat = '%a, %d-%b-%y %H:%M:%S GMT'
                else:
                    regex = re.compile(".* .* \d{4} .*")
                    if len(regex.findall(v["expires"])) != 0:
                        gmt_pormat = '%a, %d %b %Y %H:%M:%S GMT'
                    else:
                        gmt_pormat = '%a, %d %b %y %H:%M:%S GMT'
                expires = time.mktime(time.strptime(v["expires"], gmt_pormat))

            cookie = create_cookie(name=k, value=v.value, path=v["path"], domain=v["domain"], expires=expires)
            self.cookies.set_cookie(cookie)


def request_dict_to_obj(request_dict: dict):
    reuqest = Request(method="GET", url="www.baidu.com")
    for request_k, request_v in request_dict.items():
        setattr(reuqest, request_k, request_v)
    return reuqest


def get_cookies(cookies):
    cookies_str = ""
    for k, v in cookies.items():
        cookies_str = cookies_str + k + "=" + v + ";"
    return cookies_str[:-1]


def update_cookie_to_headers(headers: dict, cookies):
    if cookies is None:
        return
    cookies_str: str = headers.get("Cookie", "")
    if cookies_str == "":
        headers.update({"Cookie": get_cookies(cookies)})
        return
    if ";" in cookies_str:
        cookie_str_list: list = cookies_str.split(";")
        for cookie_str in cookie_str_list:
            if cookie_str != "":
                cookie = cookie_str.split("=")
                cook = dict()
                cook[cookie[0]] = cookie[1]
                cookies.update(cook)
    else:
        cookie = cookies_str.split("=")
        cook = dict()
        cook[cookie[0]] = cookie[1]
        cookies.update(cook)
    headers.update({"Cookie": get_cookies(cookies)})


def get_cookie_from_headers(headers: dict):
    cookies = {}
    cookies_str: str = headers.get("Cookie", "").replace(" ", "")
    if cookies_str == "":
        return cookies
    cookie_str_list: list = cookies_str.split(";")
    for cookie_str in cookie_str_list:
        if cookie_str != "":
            cookie = cookie_str.split("=")
            if len(cookie) != 2: raise Exception(f"Error Cookie in Headers! {headers}")
            cookies[cookie[0]] = cookie[1]
    return cookies


def create_cookie(name, value, domain, path, expires, **kwargs):
    """Make a cookie from underspecified parameters.

    By default, the pair of `name` and `value` will be set for the domain ''
    and sent on every request (this is sometimes called a "supercookie").
    """
    result = dict(
        version=0,
        name=name,
        value=value,
        port=None,
        domain=domain,
        path=path,
        secure=False,
        expires=expires,
        discard=True,
        comment=None,
        comment_url=None,
        rest={'HttpOnly': None},
        rfc2109=False, )
    result["expires"] = float(result["expires"])
    badargs = set(kwargs) - set(result)
    if badargs:
        err = 'create_cookie() got unexpected keyword arguments: %s'
        raise TypeError(err % list(badargs))

    result.update(kwargs)
    result['port_specified'] = bool(result['port'])
    result['domain_specified'] = bool(result['domain'])
    result['domain_initial_dot'] = result['domain'].startswith('.')
    result['path_specified'] = bool(result['path'])

    return Cookie(**result)


if __name__ == "__main__":
    v={}
    v["expires"] = "Sat, 10 Feb 2029 09:41:16 GMT"

    GMT_FORMAT = '%a, %d-%b-%y %H:%M:%S GMT'

    if v["expires"] != "":
        if "-" in v["expires"]:
            regex = re.compile(".*-.*-\d{4} .*")
            if len(regex.findall(v["expires"])) != 0:
                gmt_pormat = '%a, %d-%b-%Y %H:%M:%S GMT'
            else:
                gmt_pormat = '%a, %d-%b-%y %H:%M:%S GMT'
        else:
            regex = re.compile(".* .* \d{4} .*")
            if len(regex.findall(v["expires"])) != 0:
                gmt_pormat = '%a, %d %b %Y %H:%M:%S GMT'
            else:
                gmt_pormat = '%a, %d %b %y %H:%M:%S GMT'

        print(gmt_pormat)
        expires = time.mktime(time.strptime(v["expires"], gmt_pormat))
        print()
        print(expires)

    # print(datetime.strptime(ss, GMT_FORMAT))
