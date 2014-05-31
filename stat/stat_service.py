#! /usr/bin/env python2
# -*- coding:utf8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import json

from seventimer_dealer import SeventimerDealer
from tornado.options import define, options
define('port', default=33100, help='run on the given port', type=int)
define('config', help='use the given config file', type=str)


class StatHandler(tornado.web.RequestHandler):

    def initialize(self, dealer):
        self.dealer = dealer

    def post(self):
        reqbody = json.loads(self.request.body)
        dic = reqbody['data']
        getattr(self.dealer, reqbody['type'])(dic, self.request.remote_ip)
        if reqbody['type'] == 'start_app':
            self.write(json.dumps(self.dealer.update_info))

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[(r'/stat/seventimer', StatHandler, dict(dealer=SeventimerDealer(options.config)))])
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
