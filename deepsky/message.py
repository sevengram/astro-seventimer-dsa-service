# -*- coding:utf8 -*-

import urlparse
import urllib
import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient
import tornado.httputil
import sys
import json
import Cookie
import time

login_url = 'https://mp.weixin.qq.com/cgi-bin/login'
send_url = 'https://mp.weixin.qq.com/cgi-bin/singlesend'


class CookieManager(object):

    def __init__(self):
        self.cookie = {}

    def is_empty(self):
        return not self.cookie

    def clear(self):
        self.cookie.clear()

    def build(self):
        return ';'.join(['%s=%s' % (key, value) for key, value in self.cookie.items()])

    def set_cookie(self, headers):
        for sc in headers.get_list("Set-Cookie"):
            c = Cookie.SimpleCookie(sc)
            for morsel in c.values():
                self.cookie[morsel.key] = morsel.value


class MessageDealer(object):

    def __init__(self):
        self.token = ''
        self.last_login = 0
        self.cookie_manager = CookieManager()
        self.headers = tornado.httputil.HTTPHeaders(
            {
                "Connection": "keep-alive",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": "https://mp.weixin.qq.com",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://mp.weixin.qq.com/",
                "Accept-Encoding": "gzip,deflate,sdch",
                "Accept-Language": "zh-CN,zh;q=0.8"
            })

    def has_login(self):
        return self.token and not self.cookie_manager.is_empty() and time.time() - self.last_login < 60 * 10

    @tornado.gen.coroutine
    def post_request(self, url, data):
        client = tornado.httpclient.AsyncHTTPClient()
        self.headers.add('cookie', self.cookie_manager.build())
        body = urllib.urlencode(data)
        req = tornado.httpclient.HTTPRequest(
            url=url, method='POST', headers=self.headers, body=body, connect_timeout=60, request_timeout=60)
        res = yield client.fetch(req)
        if res.code == 200:
            self.cookie_manager.set_cookie(res.headers)
            data = json.loads(res.body)
            raise tornado.gen.Return(data)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def login(self, username, pwd):
        self.cookie_manager.clear()
        result = yield self.post_request(login_url, {'username': username, 'pwd': pwd, 'f': 'json'})
        if result and result['base_resp']['ret'] == 0:
            self.last_login = time.time()
            self.token = dict(
                urlparse.parse_qsl(result['redirect_url']))['token']
            raise tornado.gen.Return(self.token)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def send_text_message(self, fakeid, content):
        result = yield self.post_request(send_url, {
            'token': self.token, 'lang': 'zh_CN', 'f': 'json', 'ajax': 1, 'type': 1,
            'content': content.encode('utf8'), 'tofakeid': fakeid})
        raise tornado.gen.Return(result)


class MessageHandler(tornado.web.RequestHandler):

    def initialize(self, dealer):
        self.dealer = dealer
        self.username = 'sevengram'
        self.pwd = 'cbe34b794cc95deb3e5b5d390efb74d7'

    def get(self):
        self.write('empty')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        if not self.dealer.has_login():
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(status_code=500, message='fail to login')
                return

        data = self.get_argument('data')
        result = yield self.dealer.send_text_message('1899417504', data)
        if result and result['base_resp']['ret'] == -3:
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(status_code=500, message='fail to login')
                return
            result = yield self.dealer.send_text_message('1899417504', data)

        if result and result['base_resp']['ret'] == 0:
            self.write(
                json.dumps({'type': 'service@message', 'err': 0, 'msg': result['base_resp']['err_msg']}))
            self.finish()
        else:
            self.send_error(status_code=500, message='fail to send message')
        sys.stdout.flush()

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@message',
                  'err': status_code, 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
