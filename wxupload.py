# -*- coding:utf8 -*-

import sys
import json
import time

import tornado.web
import tornado.gen


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
        # check params
        filename = self.get_argument('filename', None)
        title = self.get_argument('title', None)
        content = self.get_argument('content', None)
        digest = self.get_argument('digest', '')
        author = self.get_argument('author', '')
        sourceurl = self.get_argument('sourceurl', '')
        if not filename or not title or not content:
            self.send_error(status_code=200, err=1, message='miss params')
            return

        # try login
        if not self.dealer.has_login():
            yield self.dealer.login(self.username, self.pwd)
            if not self.dealer.has_login():
                self.send_error(
                    status_code=200, err=3, message='fail to login')
                return

        # find ticket
        result = yield self.dealer.get_ticket()
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
            result = yield self.dealer.get_ticket()

        # ticket found
        if result.get('err') == 0 and result.get('msg'):
            upload_result = yield self.dealer.upload_image(result.get('msg'), filename.encode('utf-8'))
            if upload_result.get('err') == 0:
                save_result = yield self.dealer.save_material(title, content, digest, author, upload_result.get('msg'),
                                                              sourceurl)
                if save_result.get('err') == 0:
                    search_result = yield self.dealer.get_lastest_material(10, title)
                    self.write(
                        {'type': 'service@wxupload', 'err': search_result.get('err'), 'msg': search_result.get('msg')})
                    self.finish()
                    sys.stdout.flush()
                else:
                    self.send_error(status_code=200, err=save_result.get(
                        'err'), message=save_result.get('msg'))
            else:
                self.send_error(status_code=200, err=upload_result.get(
                    'err'), message=upload_result.get('msg'))
        else:
            self.send_error(status_code=200, err=result.get('err'), message=result.get('msg'))

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@wxupload',
                  'err': kwargs.get('err'), 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
