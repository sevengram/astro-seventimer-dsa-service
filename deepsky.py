# -*- coding: utf-8 -*-

import time
import datetime
import json
import sys

import pymongo
import tornado.web
import tornado.gen


class Connector(object):
    def __init__(self, debug=False):
        self.connection = pymongo.Connection('localhost', 27017)
        self.datadb = self.connection.astro_data
        self.datadb.authenticate('dsa', 'dsaeboue')
        self.userdb = self.connection.astro_users
        self.userdb.authenticate('dsa', 'dsaeboue')
        self.ssinfo = self.datadb.ssinfo
        self.csinfo = self.datadb.constellation
        self.debug = debug

    def __del__(self):
        self.connection.close()

    def autolist(self, table, username, mag, lat, typ=None):
        collection = getattr(self.datadb, table)
        query = {}
        if typ:
            query['type'] = {'$in': typ}
        if lat > 0:
            query['dec_value'] = {'$gt': lat - 90}
        else:
            query['dec_value'] = {'$lt': 90 + lat}
        query['mag'] = {'$lt': mag}
        cursor = collection.find(query)
        result = []
        while True:
            try:
                item = cursor.next()
                if 'size' not in item:
                    item['size'] = '-'
                if 'type' not in item:
                    item['type'] = 'NONEX'
                if 'con' not in item:
                    item['con'] = 'N/A'
                if 'mag' not in item:
                    item['mag'] = 99.9
                if not self.is_observerd(username, item):
                    del item['_id']
                    self.add_ssinfo(item)
                    result.append(item)
            except StopIteration:
                break
        return result

    def miss_targets(self, username, targets):
        result = []
        for target in targets:
            r = self.ssinfo.find_one({'ssid': target['ssid']})
            if r:
                if not self.is_observerd(username, r):
                    src_collection = getattr(self.datadb, r['ref'])
                    item = src_collection.find_one({'object': r['object']})
                    if item:
                        if 'size' not in item:
                            item['size'] = '-'
                        if 'type' not in item:
                            item['type'] = 'NONEX'
                        if 'con' not in item:
                            item['con'] = 'N/A'
                        if 'mag' not in item:
                            item['mag'] = 99.9
                        del item['_id']
                        item['ssinfo'] = r['skysafari_info']
                        result.append(item)
                    else:
                        print("[WARNING] No data: %s" % r['object'])
            else:
                print("[WARNING] No ssid: %s" % target['ssid'])
        return result

    def is_observerd(self, username, item):
        collection = getattr(self.userdb, username).records
        r = collection.find_one({'object': item['object']})
        return r is not None

    def add_ssinfo(self, item):
        r = self.ssinfo.find_one({'object': item['object']})
        if not r:
            r = self.ssinfo.find_one({'alias': item['object']})
        if 'alias' in item and not r:
            for alias in item['alias']:
                r = self.ssinfo.find_one({'object': alias})
                if not r:
                    r = self.ssinfo.find_one({'alias': alias})
                if r:
                    break
        if r:
            item['ssinfo'] = r['skysafari_info']
        else:
            print("[WARNING] No ssinfo: %s" % item)

    def add_skylist_record(self, username, ssid, observing_time):
        target_collection = getattr(self.userdb, username).records
        r = self.ssinfo.find_one({'ssid': ssid})
        if r:
            src_collection = getattr(self.datadb, r['ref'])
            obj = src_collection.find_one({'object': r['object']})
            if obj:
                history = target_collection.find_one({'data.id': obj['_id']})
                if not history:
                    item = {'object': obj['object'], 'history': observing_time, 'data': {
                        'database': self.datadb.name, 'collection': r['ref'], 'id': obj['_id']}}
                    if 'alias' in obj:
                        item['alias'] = obj['alias']
                    if 'mag' in obj:
                        item['mag'] = obj['mag']
                    if 'type' in obj:
                        item['type'] = obj['type']
                    print("[INFO] Add new record %s" % item)
                    self.__insert__(target_collection, item)
                elif len(observing_time) != 0:
                    print("[INFO] Add new history %s -> %s" % (observing_time, history))
                    self.__addalltoset__(target_collection, history, 'history', observing_time)
            else:
                print("[WARNING] No data: %s" % r['object'])
        else:
            print("[WARNING] No ssid: %s" % ssid)

    def __addalltoset__(self, collection, old_record, key, values):
        if self.debug:
            print('Update: %s: %s add %s' % (old_record['object'], key, values))
        else:
            collection.update({'_id': old_record['_id']}, {'$addToSet': {key: {'$each': values}}})

    def __insert__(self, collection, item):
        if self.debug:
            print("Insert: %s" % item)
        else:
            collection.insert(item)


class DeepskyHandler(tornado.web.RequestHandler):
    def initialize(self, dealer):
        self.dealer = dealer

    @tornado.gen.coroutine
    def post(self):
        try:
            reqbody = json.loads(self.request.body.decode('utf8'))
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
        except KeyError as e:
            print("[ERROR] Missing key %s: %s" % (e, self.request.body))
        except ValueError as e:
            print("[ERROR] ValueError %s: %s" % (e, self.request.body))
        finally:
            sys.stdout.flush()

    def data_received(self, chunk):
        pass


class DeepskyDealer(object):
    def __init__(self):
        self.conn = Connector(debug=False)

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
