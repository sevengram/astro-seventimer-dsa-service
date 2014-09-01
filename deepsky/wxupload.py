# -*- coding:utf8 -*-

import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient
import tornado.httputil
import sys
import json
import time


class WechatUploadHandler(tornado.web.RequestHandler):

    def initialize(self, dealer):
        self.dealer = dealer
        self.username = 'sevengram'
        self.pwd = 'cbe34b794cc95deb3e5b5d390efb74d7'

    def get(self):
        self.write('empty')

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        # try login
        if not self.dealer.has_login():
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(
                    status_code=200, err=3, message='fail to login')
                return

        # find ticket
        ticket = None
        result = yield self.dealer.get_ticket()
        if result and result.get('err') == 6:
            # login expired, retry
            print 'login expired, retry...', time.ctime()
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                print 'login retry fail', time.ctime()
                self.send_error(
                    status_code=200, err=3,  message='fail to login')
                return
            print 'login retry success', time.ctime()
            result = yield self.dealer.get_ticket()
        ticket = result.get('msg')

        if result:
            result = yield self.dealer.upload_image(ticket, '/home/jfan/1.jpg')
            self.write(result)
            self.finish()
        else:
            self.write('err')
            self.finish()
        sys.stdout.flush()

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@wxmessage',
                  'err': kwargs.get('err'), 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
