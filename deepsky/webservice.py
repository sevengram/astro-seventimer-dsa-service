#! /usr/bin/env python2
# -*- coding:utf8 -*-

import tornado.httpserver
import tornado.ioloop
import tornado.options

import deepsky
import seventimer
import wechat
import wxmessage
import wxuser

from tornado.options import define, options
from util import wxclient

define("port", default=33600, help="run on the given port", type=int)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    wechat_connector = wxclient.WechatConnector()
    app = tornado.web.Application(
        handlers=[
            (r'/service/weather', seventimer.WeatherHandler),
            (r'/service/wechat', wechat.WechatHandler),
            (r'/service/wxmessage', wxmessage.WechatMsgHandler, dict(dealer=wechat_connector)),
            (r'/service/wxuser', wxuser.WechatUsrHandler, dict(dealer=wechat_connector)),
            (r'/service/dsa', deepsky.DeepskyHandler, dict(dealer=deepsky.DeepskyDealer()))
            ], debug=True)
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
