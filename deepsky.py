# -*- coding:utf8 -*-

import time
import datetime
import json
import sys

import tornado.web

from util import mongo


class DeepskyHandler(tornado.web.RequestHandler):
    def initialize(self, dealer):
        self.dealer = dealer

    def get(self):
        self.write('hello world')

    def post(self):
        try:
            reqbody = json.loads(self.request.body)
            if reqbody['type'] == 'query':
                query = reqbody['param']
                print("[QUERY]: %s" % query)
                result = self.dealer.userlist(
                    query['user'], query['mag'], query['lat'], typ=query['type'])
                self.set_header('content-type', 'text/plain')
                self.write(json.dumps(result))
            elif reqbody['type'] == 'upload':
                upload = reqbody['param']
                print("[UPLOAD]: %s" % upload)
                self.dealer.upload_record(upload['user'], upload['records'])
                result = self.dealer.get_miss_targets(
                    upload['user'], upload['remains'])
                self.set_header('content-type', 'text/plain')
                self.write(json.dumps(result))
            else:
                print("[WARNING] Unknown request type: %s" % self.request.body)
        except KeyError, e:
            print("[ERROR] Missing key %s: %s" % (e, self.request.body))
        except ValueError, e:
            print("[ERROR] ValueError %s: %s" % (e, self.request.body))
        finally:
            sys.stdout.flush()


class DeepskyDealer(object):
    def __init__(self):
        self.conn = mongo.Connector(debug=False)

    def userlist(self, username, mag, lat, typ=None):
        return self.conn.autolist('deepsky', username, mag, lat, typ)

    def upload_record(self, username, records):
        for record in records:
            t = time.gmtime(
                (float(record['DateObserved']) - 2440587.5) * 3600 * 24)
            observing_time = [datetime.datetime(*t[:6])]
            self.conn.add_skylist_record(
                username, record['ssid'], observing_time)

    def get_miss_targets(self, username, targets):
        return self.conn.miss_targets(username, targets)
