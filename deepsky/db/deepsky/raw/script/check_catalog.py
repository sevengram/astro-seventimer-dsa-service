#! /usr/bin/env python2
# -*- coding:utf8 -*-

import pymongo
import sys

connection = pymongo.Connection('localhost', 27017)
datadb = connection.astro_data
userdb = connection.astro_users

records = getattr(userdb, sys.argv[1]).records
items = getattr(datadb.catalogs, sys.argv[2])

count = 0
for item in items.find():
    count += (records.find_one({'object':datadb.dereference(item['data'])['object']}) != None)
print('%d/%d' % (count, items.count()))

connection.close()