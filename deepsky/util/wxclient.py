# -*- coding:utf8 -*-

import urlparse
import urllib
import tornado.gen
import tornado.httpclient
import tornado.httputil
import json
import Cookie
import time
import sys
import random

from bs4 import BeautifulSoup

base_url = 'https://mp.weixin.qq.com/'

home_url = base_url + 'cgi-bin/home'

login_url = base_url + 'cgi-bin/login'

send_url = base_url + 'cgi-bin/singlesend'

message_url = base_url + 'cgi-bin/message'

send_page_url = base_url + 'cgi-bin/singlesendpage'

common_headers = tornado.httputil.HTTPHeaders(
    {
        "Connection": "keep-alive",
        "Origin": base_url,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "zh-CN,zh;q=0.8"
    })


class CookieManager(object):

    def __init__(self):
        self.cookie = {'data_bizuin': '2393201154', 'slave_user': 'gh_d188e2888313',
                       'bizuin': '2391209664'}

    def is_empty(self):
        return self.cookie.get('slave_sid', '') == '' or self.cookie.get('data_ticket', '') == ''

    def clear(self):
        self.cookie = {'data_bizuin': '2393201154', 'slave_user': 'gh_d188e2888313',
                       'bizuin': '2391209664'}

    def build(self):
        return ';'.join(['%s=%s' % (key, value) for key, value in self.cookie.items()])

    def set_cookie(self, headers):
        for sc in headers.get_list("Set-Cookie"):
            c = Cookie.SimpleCookie(sc)
            for morsel in c.values():
                if morsel.key not in ['data_bizuin', 'slave_user', 'bizuin']:
                    if morsel.value and morsel.value != 'EXPIRED':
                        self.cookie[morsel.key] = morsel.value
                    else:
                        self.cookie.pop(morsel.key, None)
        print 'Cookie updated:', self.cookie


class WechatConnector(object):

    def __init__(self):
        self.token = ''
        self.last_login = 0
        self.cookie_manager = CookieManager()

    def has_login(self):
        return self.token and not self.cookie_manager.is_empty() and time.time() - self.last_login < 60 * 10

    @tornado.gen.coroutine
    def post_request(self, url, data, **kwargs):
        headers = common_headers.copy()
        headers.add('Cookie', self.cookie_manager.build())
        headers.add('Accept', 'application/json, text/javascript, */*; q=0.01')
        headers.add('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        headers.add('Referer', kwargs.get('referer', base_url))

        client = tornado.httpclient.AsyncHTTPClient()
        print 'Weixin POST url: %s\nheaders: %s\ndata: %s' % (url, headers, data)

        req = tornado.httpclient.HTTPRequest(
            url=url, method='POST', headers=headers, body=urllib.urlencode(data), connect_timeout=60, request_timeout=60)
        res = yield client.fetch(req)
        if res.code == 200:
            self.cookie_manager.set_cookie(res.headers)
            data = json.loads(res.body, encoding='utf-8')
            print 'Response: ', data
            sys.stdout.flush()
            raise tornado.gen.Return(data)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def get_request(self, url, data, **kwargs):
        headers = common_headers.copy()
        headers.add('Cookie', self.cookie_manager.build())
        headers.add(
            'Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        headers.add('Referer', kwargs.get('referer', base_url))

        client = tornado.httpclient.AsyncHTTPClient()
        url += '?' + urllib.urlencode(data)
        print 'Wexin GET url: %s\nheaders: %s' % (url, headers)

        req = tornado.httpclient.HTTPRequest(
            url=url, method='GET', headers=headers, connect_timeout=60, request_timeout=60)
        res = yield client.fetch(req)
        if res.code == 200:
            self.cookie_manager.set_cookie(res.headers)
            raise tornado.gen.Return(res.body)
        else:
            raise tornado.gen.Return(None)

    @tornado.gen.coroutine
    def login(self, username, pwd):
        # self.cookie_manager.clear()
        print 'try login...'
        result = yield self.post_request(login_url, {'username': username, 'pwd': pwd, 'f': 'json'})
        if result and result['base_resp']['ret'] == 0:
            self.last_login = time.time()
            self.token = dict(
                urlparse.parse_qsl(result['redirect_url']))['token']
            print 'login success, new token:', self.token
            raise tornado.gen.Return(self.token)
        else:
            print 'login failed'
            raise tornado.gen.Return(None)

    def _check_same(self, timestamp, content, mtype, user):
        if mtype == 'text' and content:
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
        referer = home_url + '?' + \
            urllib.urlencode({'t': 'home/index', 'token': self.token, 'lang': 'zh_CN'})
        result = yield self.get_request(message_url, {
            'count': count, 'offset': offset, 'day': 7, 'token': self.token}, referer=referer)
        raw = BeautifulSoup(result)
        try:
            t = raw.find_all(
                'script', {'type': 'text/javascript', 'src': ''})[-1].text
            users = json.loads(
                t[t.index('['):t.rindex(']') + 1], encoding='utf-8')
        except (ValueError, IndexError):
            users = None

        if not users:
            if raw.find('div', {'class': 'msg_content'}).text.strip().startswith(u'\u767b'):
                print 'find_user failed: login expired'
                sys.stdout.flush()
                raise tornado.gen.Return({'err': 6, 'msg': 'login expired'})
            else:
                print 'find_user failed'
                sys.stdout.flush()
                raise tornado.gen.Return({'err': 4, 'msg': 'fail to find user'})
        for i in range(0, len(users) - 1):
            if users[i]['date_time'] < timestamp:
                print 'find_user failed: no match 1'
                sys.stdout.flush()
                raise tornado.gen.Return({'err': 4, 'msg': 'fail to find user'})
            elif self._check_same(timestamp, content, mtype, users[i]):
                if not self._check_same(timestamp, content, mtype, users[i + 1]):
                    print 'find_user success: ', users[i]
                    sys.stdout.flush()
                    raise tornado.gen.Return({'err': 0, 'msg': users[i]})
                else:
                    print 'find_user failed: no match 2'
                    sys.stdout.flush()
                    raise tornado.gen.Return({'err': 4, 'msg': 'fail to find user'})
        res = yield self.find_user(timestamp, content, mtype, count, count + offset - 1)
        raise tornado.gen.Return(res)

    @tornado.gen.coroutine
    def send_text_message(self, fakeid, content):
        url = send_url + '?' + \
            urllib.urlencode(
                {'t': 'ajax-response', 'f': 'json', 'token': self.token, 'lang': 'zh_CN'})
        referer = send_page_url + '?' + \
            urllib.urlencode(
                {'tofakeid': fakeid, 't': 'message/send', 'action': 'index', 'token': self.token, 'lang': 'zh_CN'})
        result = yield self.post_request(url, {
            'token': self.token, 'lang': 'zh_CN', 'f': 'json', 'ajax': 1, 'type': 1,
            'content': content.encode('utf-8'), 'tofakeid': fakeid, 'random': random.random()}, referer=referer)
        print 'send_text_message response', result
        sys.stdout.flush()
        try:
            if result['base_resp']['ret'] == -3:
                raise tornado.gen.Return({'err': 6, 'msg': 'login expired'})
            elif result['base_resp']['ret'] == 0:
                raise tornado.gen.Return({'err': 0, 'msg': result['base_resp']['err_msg']})
            else:
                raise tornado.gen.Return({'err': 5, 'msg': result['base_resp']['err_msg']})
        except (KeyError, AttributeError, TypeError):
            raise tornado.gen.Return({'err': 5, 'msg': 'fail to send message'})
