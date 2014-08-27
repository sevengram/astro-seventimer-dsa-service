# -*- coding:utf8 -*-

import urlparse
import urllib
import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient
import tornado.httputil
import json
import Cookie
import time

from bs4 import BeautifulSoup

login_url = 'https://mp.weixin.qq.com/cgi-bin/login'
send_url = 'https://mp.weixin.qq.com/cgi-bin/singlesend'
message_url = 'https://mp.weixin.qq.com/cgi-bin/message'


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


class WechatConnector(object):

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
            data = json.loads(res.body, encoding='utf-8')
            raise tornado.gen.Return(data)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def get_request(self, url, data):
        client = tornado.httpclient.AsyncHTTPClient()
        self.headers.add('cookie', self.cookie_manager.build())
        url += '?' + urllib.urlencode(data)
        req = tornado.httpclient.HTTPRequest(
            url=url, method='GET', headers=self.headers, connect_timeout=60, request_timeout=60)
        res = yield client.fetch(req)
        if res.code == 200:
            self.cookie_manager.set_cookie(res.headers)
            raise tornado.gen.Return(res.body)
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

    def _check_same(self, timestamp, content, mtype, user):
        if mtype == 'text':
            return user['date_time'] == timestamp and user['content'].strip(' \t\r\n') == content.strip(' \t\r\n') and user['type'] == 1
        elif mtype == 'location':
            return user['date_time'] == timestamp and user['content'].startswith(
                'http://weixin.qq.com/cgi-bin/redirectforward') and user['type'] == 1
        elif mtype == 'image':
            return user['date_time'] == timestamp and user['type'] == 2
        else:
            return False

    @tornado.gen.coroutine
    def find_user(self, timestamp, content, mtype, count, offset):
        result = yield self.get_request(message_url, {
            'count': count, 'offset': offset, 'day': 7, 'token': self.token})
        try:
            t = BeautifulSoup(result).find_all(
                'script', {'type': 'text/javascript', 'src': ''})[-1].text
            users = json.loads(
                t[t.index('['):t.rindex(']') + 1], encoding='utf-8')
        except (ValueError, IndexError):
            raise tornado.gen.Return(None)

        if not users:
            raise tornado.gen.Return(None)
        for i in range(0, len(users) - 1):
            if users[i]['date_time'] < timestamp:
                raise tornado.gen.Return(None)
            elif self._check_same(timestamp, content, mtype, users[i]):
                if not self._check_same(timestamp, content, mtype, users[i + 1]):
                    raise tornado.gen.Return(users[i])
                else:
                    raise tornado.gen.Return(None)
        res = yield self.find_user(timestamp, content, mtype, count, count + offset - 1)
        raise tornado.gen.Return(res)

    @tornado.gen.coroutine
    def send_text_message(self, fakeid, content):
        result = yield self.post_request(send_url, {
            'token': self.token, 'lang': 'zh_CN', 'f': 'json', 'ajax': 1, 'type': 1,
            'content': content.encode('utf8'), 'tofakeid': fakeid})
        raise tornado.gen.Return(result)
