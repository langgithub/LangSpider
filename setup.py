#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/7/16 下午5:57
# file: setup.py

from setuptools import setup

setup(name="LangSpider",
      version="1.0",
      description="spider module",
      author="yuanlang",
      author_email='15775691981@163.com',
      url='https://github.com/langgithub/LangSpider',
      packages=[
          'lang_spider',
      ],
      license='MIT License',
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      python_requires='>=3.6',
)
