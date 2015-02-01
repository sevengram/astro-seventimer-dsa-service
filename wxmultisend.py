# -*- coding:utf8 -*-

import sys
import json
import time

import tornado.web
import tornado.gen


class WechatMultiSendHandler(tornado.web.RequestHandler):
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
        appmsgid = self.get_argument('appmsgid', None)
        groupid = self.get_argument('groupid', -1)
        if not appmsgid:
            self.send_error(status_code=200, err=1, message='miss params')
            return

        # try login
        if not self.dealer.has_login():
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(
                    status_code=200, err=3, message='fail to login')
                return

        # find seq
        result = yield self.dealer.get_operation_seq()
        if result and result.get('err') == 6:
            # login expired, retry
            print 'login expired, retry...', time.ctime()
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                print 'login retry fail', time.ctime()
                self.send_error(
                    status_code=200, err=3, message='fail to login')
                return
            print 'login retry success', time.ctime()
            result = yield self.dealer.get_operation_seq()

        # seq found
        if result.get('err') == 0:
            send_result = yield self.dealer.multi_send_message(result.get('msg'), appmsgid, groupid)
            self.write(
                {'type': 'service@wxmultisend', 'err': send_result.get('err'), 'msg': send_result.get('msg')})
            self.finish()
            sys.stdout.flush()
        else:
            self.send_error(
                status_code=200, err=result.get('err'), message=result.get('msg'))

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@wxmultisend',
                  'err': kwargs.get('err'), 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
