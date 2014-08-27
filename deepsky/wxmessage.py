# -*- coding:utf8 -*-

import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient
import tornado.httputil
import sys
import json
import urllib


class WechatMsgHandler(tornado.web.RequestHandler):

    def initialize(self, dealer):
        self.dealer = dealer
        self.username = 'sevengram'
        self.pwd = 'cbe34b794cc95deb3e5b5d390efb74d7'

    def get(self):
        self.write('empty')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        # check params
        message = self.get_argument('message')
        userinfo = self.get_argument('userinfo')
        if not message or not userinfo:
            self.send_error(status_code=200, err=1, message='miss params')
            return

        # try login
        if not self.dealer.has_login():
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(
                    status_code=200, err=3, message='fail to login')
                return

        # ask for fakeid
        fakeid = None
        client = tornado.httpclient.AsyncHTTPClient()
        req = tornado.httpclient.HTTPRequest(
            url='http://127.0.0.1/service/wxuser?' +
                urllib.urlencode(
                    {'cached': 1, 'userinfo': userinfo.encode('utf-8')}),
            method='GET', headers={}, connect_timeout=30, request_timeout=120)
        res = yield client.fetch(req)
        if res.code == 200:
            data = json.loads(res.body, encoding='utf-8')
            if data.get('err') == 0:
                fakeid = data.get('msg')
        if not fakeid:
            self.send_error(status_code=200, err=4, message='fail to find user')
            return

        # send message to wechat user
        result = yield self.dealer.send_text_message(fakeid, message)
        if result and result.get('err') == 6:
            # login expired, retry
            print 'login expired, retry...'
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(
                    status_code=200, err=3,  message='fail to login')
                return
            result = yield self.dealer.send_text_message(fakeid, message)

        # request to service user
        if result and result.get('err') == 0:
            self.write(
                json.dumps({'type': 'service@wxmessage', 'err': 0, 'msg': result.get('msg', 'ok')}))
            self.finish()
        else:
            self.send_error(
                status_code=200, err=5, message=result.get('msg', 'fail to send message'))
        sys.stdout.flush()

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@wxmessage',
                  'err': kwargs.get('err'), 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
