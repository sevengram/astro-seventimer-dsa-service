#! /usr/bin/env python2
# -*- coding:utf8 -*-

import pymongo
import datetime

connection = pymongo.Connection('localhost', 27017)
datadb = connection.astro_data
userdb = connection.astro_users

records = userdb.fjx.records

results = records.find({'history':{'$gt':datetime.datetime(2013, 9, 21, 00, 00)}})

for result in results:
	print result

connection.close()