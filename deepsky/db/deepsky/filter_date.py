#! /usr/bin/env python2
# -*- coding:utf8 -*-

import pymongo
import datetime

connection = pymongo.Connection('localhost', 27017)
datadb = connection.astro_data
userdb = connection.astro_users

records = userdb.fjx.records
data = datadb.deepsky

results = records.find({'history':{'$gt':datetime.datetime(2013, 9, 28, 00, 00)}})
print results.count()
for result in results:
    d = data.find_one({'_id':result['data']['id']})
    if d != None:
        print d
        alias = []
        if d.has_key('alias'): alias = d['alias']
        # print('%s  %s  %.1f  %s  %s  %s' % (d['object'], d['type'], d['mag'], d['size'], d['con'], alias))
    else:
        print 'No record!'

connection.close()
