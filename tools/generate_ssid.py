#! /usr/bin/env python2
# -*- coding:utf8 -*-

import hashlib
from pymongo import MongoClient

if __name__ == "__main__":
    client = MongoClient('localhost', 27017)
    db = client.astro_data
    for info in db.ssinfo.find():
        numbers = info['skysafari_info']['CatalogNumber']
        numbers.sort()
        ssid = hashlib.md5(''.join(numbers).replace(' ', '').lower()).hexdigest().lower()
        db.ssinfo.update({'_id': info['_id']}, {'$set': {'ssid': ssid}})