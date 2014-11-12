#! /usr/bin/env python2
# -*- coding:utf8 -*-

import pymongo

connection = pymongo.Connection('localhost', 27017)
datadb = connection.astro_data
userdb = connection.astro_users

records = userdb.fjx.records
items = datadb.deepsky

for record in records.find():
    item = items.find_one({'_id':record['data']['id']})
    records.update({'object':item['object']}, {'$set':{'mag':item['mag'],'type':item['type']}})
    
connection.close()
