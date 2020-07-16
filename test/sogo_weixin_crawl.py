#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/7/16 上午10:34
# file: sogo_weixin_crawl.py

#
# import requests
# def parse(response: requests.Response):
#     pass
#
#
# import requests
#
# keyword = "平安银行"
# url = "https://weixin.sogou.com/weixin?query={0}&_sug_type_=&s_from=input&_sug_=n&type=2&page={1}&ie=utf8"
# # 只能取到100页
# for page in range(1, 101):
#     # 不登陆获取10页，登陆只能获取到100页。登陆cookie写死
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
#         "Cookie": "ABTEST=1|1594809155|v1; IPLOC=CN1100; SUID=83E7C66F541CA00A000000005F0EDB43; SUID=83E7C66F3121A00A000000005F0EDB43; weixinIndexVisited=1; SUV=00406AA66FC6E7835F0EDB44F1AF4864; sct=1; SNUID=395D7CD6BABC13C21BCAA250BA31E910; usid=x2H_7-KgVxUJD0RC; wuid=AAFDd7wIMAAAAAqPLE2IKwAA1wA=; FREQUENCY=1594810600142_1; front_screen_resolution=1080*1920; sgwtype=3; CXID=B33431FFC120C508C61F52FFEAF822B0; ld=FZllllllll2KRmRXlllllVDnc5YlllllbDbXkZllllwlllllRZlll5@@@@@@@@@@; JSESSIONID=aaaSstUTXux6XfohbrYmx; ppinf=5|1594869425|1596079025|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyOmRwfGNydDoxMDoxNTk0ODY5NDI1fHJlZm5pY2s6MjpkcHx1c2VyaWQ6NDQ6bzl0Mmx1QUZmRjZqdkVpbFltOGJxcGFBaUpBMEB3ZWl4aW4uc29odS5jb218; pprdig=LDJWy_4YA-h4NlxVZAqBwIDJd6x52DbAjfnBnWrH7gNHAYxbQVVB1EN8smjFdJtCAcYgaB6v4Y5NcRf6T7RSht416iGHtFyp-Sqwzft_lQQdyiJvHvtdHNfJXb5Aqj6RH1WHiwbGQ-r3fi7Y_5xVmgxKsYhyS9M07dR5WtzA1BI; sgid=27-48968505-AV8PxrHhXDE0uKrWVFC5Agc; ppmdig=1594869425000000f2f601c4e0bd76effab01455eb65c1f5"
#     }
#     response = requests.get(url.format(keyword, page), verify=False, headers=headers)
#     response.encoding = "utf-8"
#     print(response.text)
import os
import time
import json
import base64
from scrapy import Selector
from lang_spider.sync_spider import SyncSpider
from lang_spider.web_http import Request


class SogoWeixinCrawl(SyncSpider):

    other_cookies = "ABTEST=1|1594809155|v1; IPLOC=CN1100; SUID=83E7C66F541CA00A000000005F0EDB43; SUID=83E7C66F3121A00A000000005F0EDB43; weixinIndexVisited=1; sct=1; usid=x2H_7-KgVxUJD0RC; wuid=AAFDd7wIMAAAAAqPLE2IKwAA1wA=; FREQUENCY=1594810600142_1; front_screen_resolution=1080*1920; sgwtype=3; CXID=B33431FFC120C508C61F52FFEAF822B0; ld=FZllllllll2KRmRXlllllVDnc5YlllllbDbXkZllllwlllllRZlll5@@@@@@@@@@; JSESSIONID=aaaSstUTXux6XfohbrYmx; ppinf=5|1594869425|1596079025|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToyOmRwfGNydDoxMDoxNTk0ODY5NDI1fHJlZm5pY2s6MjpkcHx1c2VyaWQ6NDQ6bzl0Mmx1QUZmRjZqdkVpbFltOGJxcGFBaUpBMEB3ZWl4aW4uc29odS5jb218; pprdig=LDJWy_4YA-h4NlxVZAqBwIDJd6x52DbAjfnBnWrH7gNHAYxbQVVB1EN8smjFdJtCAcYgaB6v4Y5NcRf6T7RSht416iGHtFyp-Sqwzft_lQQdyiJvHvtdHNfJXb5Aqj6RH1WHiwbGQ-r3fi7Y_5xVmgxKsYhyS9M07dR5WtzA1BI; sgid=27-48968505-AV8PxrHhXDE0uKrWVFC5Agc; PHPSESSID=vmtodnf46q480pp1hk4mq9m7o1; ppmdig=1594879680000000a34f89a28f0c3437ebbe7fa6fb5cf898"
    current_cookie = ";SNUID=7DD09D210602AC8F8F83033607DC4469;SUV=00406AA66FC6E7835F0EDB44F1AF4864;"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
    }
    headers.update({"Cookie": other_cookies + current_cookie})
    authcode_path = os.path.dirname(os.path.dirname(__file__)) + "/img/"

    def start_request(self):
        keyword = "平安银行"
        url = "https://weixin.sogou.com/weixin?query={0}&_sug_type_=&s_from=input&_sug_=n&type=2&page={1}&ie=utf8"
        # 只能取到100页
        for page in range(14, 16):
            # 不登陆获取10页，登陆只能获取到100页。登陆cookie写死
            self.add_request(Request(url=url.format(keyword, page), method="GET", verify=False, headers=self.headers, encoding="utf-8", allow_redirects=False))

    def parse(self, response):
        self.captcha_check(response)
        html = Selector(text=response.text)
        lis = html.css("ul.news-list > li")
        for li in lis:
            txt_box = li.css(".txt-box")
            a = "https://weixin.sogou.com"+txt_box.css("h3 a::attr(href)").extract_first()
            t = txt_box.css("div.s-p::attr(t)").extract_first()
            _meta = {"time": t}
            self.add_request(Request(url=a, method="GET", verify=False, headers=self.headers, meta=_meta, callback=self.prase_url))

    def prase_url(self, response):
        self.captcha_check(response)
        html = Selector(text=response.text)
        text = html.re("var url = '';([\s\S]*?)url.replace")[0].replace("\r\n", "").replace(" ", "")
        url_list = text.split(";")
        url = "".join([(url_text.split("+=")[1].replace("\'", "")) for url_text in url_list if url_text != ""])
        self.add_request(Request(url=url, method="GET", verify=False, headers=self.headers, callback=self.prase_content, meta=response.meta))

    def prase_content(self, response):
        self.captcha_check(response)
        html = Selector(text=response.text)
        content = html.css("#js_content").extract_first()
        print(response.meta)
        print(content)

    def captcha_check(self, resp):
        if "请输入验证码" in resp.text or (resp.status_code == 302 and "weixin.sogou.com/antispider/?from=" in resp.headers.get("Location","")):
            print("请输入验证码")
            # 获取到新cookies 跟新cookie
            while True:
                t_headers = {
                    "Referer": resp.url,
                }
                self.headers.update(t_headers)
                url = "https://weixin.sogou.com/antispider/util/seccode.php?tc=1594883063593"
                response = self.session.get(url, headers=self.headers, verify=False)
                self.save_byte("sogo", response.content)
                yzm = input("输入验证码:")
                data = {
                    "c": yzm,
                    "r": url.replace("https://weixin.sogou.com/", ""),
                    "v": "5",
                    "suuid": "",
                    "auuid": resp.headers["uuid"].split(",")[0]
                }
                response = self.session.post(url="https://weixin.sogou.com/antispider/thank.php", verify=False, data=data, headers=self.headers)
                response.encoding = "utf-8"
                if "验证码输入错误, 请重新输入！" in response.text:
                    print("验证码输入错误, 请重新输入！")
                    continue
                rj = json.loads(response.text)
                self.current_cookie = ";SNUID={0};SUV={1};".format(rj["id"], "00D80B85458CAE4B5B299A407EA3A580")
                self.headers.update({"Cookie": self.other_cookies+self.current_cookie})
                break
            return True
        else:
            return False

    def save_byte(self, name, bs):
        """保存图片"""
        suffix = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        path1 = self.authcode_path + suffix
        filename = path1 + "/" + self.create_name(name)
        if not os.path.exists(path1):
            os.makedirs(path1)
        if type(bs) == str:
            bs = base64.urlsafe_b64decode(bs + '=' * (4 - len(bs) % 4))
        with open(filename, "wb") as f:
            f.write(bs)
        return filename

    @staticmethod
    def create_name(name):
        return "img" + name + "_%d" % (time.time() * 1000) + ".png"


s = SogoWeixinCrawl()
s.run()