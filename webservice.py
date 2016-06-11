#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.options import define, options

import deepsky
import seventimer

define("port", default=33600, help="run on the given port", type=int)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r'/weather', seventimer.WeatherHandler),
            (r'/dsa', deepsky.DeepskyHandler, dict(dealer=deepsky.DeepskyDealer()))
        ], debug=True)
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
