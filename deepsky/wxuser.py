# -*- coding:utf8 -*-

import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient
import tornado.httputil
import sys
import json

from util import mysql


class WechatUsrHandler(tornado.web.RequestHandler):

    def initialize(self, dealer):
        self.mysql_conn = mysql.WechatConnector()
        self.dealer = dealer
        self.username = 'sevengram'
        self.pwd = 'cbe34b794cc95deb3e5b5d390efb74d7'

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # check params
        userinfo = self.get_argument('userinfo')
        cached = self.get_argument('cached')
        if not userinfo or not cached:
            self.send_error(status_code=200, err=1, message='miss params')
            return
        try:
            userdict = json.loads(userinfo)
            openid = userdict.get('uid')
            content = userdict.get('content')
            timestamp = userdict.get('timestamp')
            mtype = userdict.get('type')
            if not openid or not timestamp or not mtype:
                self.send_error(status_code=200, err=1, message='miss params')
                return
        except ValueError:
            self.send_error(
                status_code=200, err=2, message='json format error')
            return

        fakeid = None
        # try cache
        if cached:
            query_result = self.mysql_conn.get_fakeid(openid)
            if query_result:
                fakeid = query_result.get('fakeid')

        # cache missed
        if not fakeid:
            # try login
            if not self.dealer.has_login():
                yield self.dealer.login(self.username, self.pwd)
                if not self.dealer.has_login():
                    self.send_error(
                        status_code=200, err=3, message='fail to login')
                    return

            # find user
            result = yield self.dealer.find_user(timestamp, content, mtype, 30, 0)
            if result and result.get('err') == 6:
                # login expired, retry
                print 'login expired, retry...'
                yield self.dealer.login(self.username, self.pwd)
                if not self.dealer.has_login():
                    self.send_error(
                        status_code=200, err=3,  message='fail to login')
                    return
                result = yield self.dealer.find_user(timestamp, content, mtype, 30, 0)

            # user found
            if result and result.get('err') == 0 and result.get('msg'):
                data = result.get('msg')
                fakeid = data.get('fakeid')
                # add cache
                self.mysql_conn.add_user(
                    {'uid': openid, 'fakeid': fakeid, 'nickname': data.get('nick_name')})

        # send request
        if fakeid:
            self.write(
                json.dumps({'type': 'service@wxuser', 'err': 0, 'msg': fakeid}))
            self.finish()
            sys.stdout.flush()
        else:
            self.send_error(
                status_code=200, err=4, message='fail to find user')

    def post(self):
        self.write('empty')

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@wxuser',
                  'err': kwargs.get('err'), 'msg': kwargs.get('message')}
        self.write(json.dumps(result))
        sys.stdout.flush()
