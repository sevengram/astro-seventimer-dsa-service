#! /usr/bin/env python2
# -*- coding:utf8 -*-

import re
import sys
from util import mongo

connector = mongo.Connector(debug=True)
collection = connector.datadb.deepsky
cursor = collection.find({'object':re.compile('^UGC')})
count = 0
while True:
    try:
        r = cursor.next()
        if collection.find_one({'alias':r['object']}) != None:
            print r
            #collection.remove({'_id':r['_id']})
            count += 1
    except StopIteration, e:
        break
print count


