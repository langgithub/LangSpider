#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# author：yuanlang
# creat_time: 2020/7/16 上午10:34
# file: utils.py

import hashlib

import click

def get_redis_task_key_name(site_type, crawl_type):
    return '{}_{}_tasks'.format(site_type, crawl_type)

def get_headers_from_text(text):
    headers = {}
    for line in text.split('\n'):
        line = line.strip()
        if line:
            try:
                key = line.split(':')[0].strip()
                value = line[len(key)+1:].strip()
                headers[key] = value
            except Exception as e:
                pass
    return headers

def get_cookies_from_text(text):
    cookies={}#初始化cookies字典变量
    for line in text.split(';'):   #按照字符：进行划分读取
        #其设置为1就会把字符串拆分成2份
        name,value=line.strip().split('=',1)
        cookies[name]=value  #为字典cookies添加内容
    return cookies


def echo_help():
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


# md5加密
def md5(src):
    if isinstance(src, str):
        src = src.encode('utf-8')
    m = hashlib.md5()
    m.update(src)
    return m.hexdigest()


def run():
    pass


if __name__ == '__main__':
    run()
