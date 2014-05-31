# -*- coding:utf8 -*-

import pymongo


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

    def autolist(self, table, username, mag, lat, typ=[]):
        collection = getattr(self.datadb, table)
        query = {}
        if len(typ) != 0:
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
                if not item.has_key('size'):
                    item['size'] = '-'
                if not item.has_key('type'):
                    item['type'] = 'NONEX'
                if not item.has_key('con'):
                    item['con'] = 'N/A'
                if not item.has_key('mag'):
                    item['mag'] = 99.9
                if not self.is_observerd(username, item):
                    del item['_id']
                    self.add_ssinfo(item)
                    result.append(item)
            except StopIteration, e:
                break
        return result

    def miss_targets(self, username, targets):
        result = []
        for target in targets:
            r = self.ssinfo.find_one({'skysafari_info.ObjectID': target['ObjectID']})
            if r != None:
                if not self.is_observerd(username, r):
                    src_collection = getattr(self.datadb, r['ref'])
                    item = src_collection.find_one({'object': r['object']})
                    if item != None:
                        if not item.has_key('size'):
                            item['size'] = '-'
                        if not item.has_key('type'):
                            item['type'] = 'NONEX'
                        if not item.has_key('con'):
                            item['con'] = 'N/A'
                        if not item.has_key('mag'):
                            item['mag'] = 99.9
                        del item['_id']
                        item['ssinfo'] = r['skysafari_info']
                        result.append(item)
                    else:
                        print("[WARNING] No data: %s" % r['object'])
            else:
                print("[WARNING] No ObjectID: %s" % target['ObjectID'])
        return result

    def is_observerd(self, username, item):
        collection = getattr(self.userdb, username).records
        r = collection.find_one({'object': item['object']})
        return r != None

    def add_ssinfo(self, item):
        r = self.ssinfo.find_one({'object': item['object']})
        if not r:
            r = self.ssinfo.find_one({'alias': item['object']})
        if item.has_key('alias') and not r:
            for alias in item['alias']:
                r = self.ssinfo.find_one({'object': alias})
                if not r:
                    r = self.ssinfo.find_one({'alias': alias})
                if r != None:
                    break
        if r != None:
            item['ssinfo'] = r['skysafari_info']
        else:
            print("[WARNING] No ssinfo: %s" % item)

    def add_skylist_record(self, username, ssid, observing_time):
        target_collection = getattr(self.userdb, username).records
        r = self.ssinfo.find_one({'skysafari_info.ObjectID': ssid})
        if r != None:
            src_collection = getattr(self.datadb, r['ref'])
            obj = src_collection.find_one({'object': r['object']})
            if obj != None:
                history = target_collection.find_one({'data.id': obj['_id']})
                if not history:
                    item = {'object': obj['object'], 'history': observing_time, 'data': {
                            'database': self.datadb.name, 'collection': r['ref'], 'id': obj['_id']}}
                    if obj.has_key('alias'):
                        item['alias'] = obj['alias']
                    if obj.has_key('mag'):
                        item['mag'] = obj['mag']
                    if obj.has_key('type'):
                        item['type'] = obj['type']
                    print("[INFO] Add new record %s" % item)
                    self.__insert__(target_collection, item)
                elif len(observing_time) != 0:
                    print("[INFO] Add new history %s -> %s" % (observing_time, history))
                    self.__addalltoset__(target_collection, history, 'history', observing_time)
            else:
                print("[WARNING] No data: %s" % r['object'])
        else:
            print("[WARNING] No ObjectID: %s" % ssid)

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
