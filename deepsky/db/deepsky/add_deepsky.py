#! /usr/bin/env python2
# -*- coding:utf8 -*-

import pymongo
import sys
from util import http

grabber = http.SimpleUrlGrabber()

image_url_format = 'http://www.mydeepsky.com/image/deepsky/%s'


class Connector(object):

    def __init__(self, debug=True):
        self.connection = pymongo.Connection('localhost', 27017)
        self.datadb = self.connection.astro_data
        self.datadb.authenticate('dsa', 'dsaeboue')
        self.deepsky = self.datadb.deepsky
        self.debug = debug

    def __del__(self):
        self.connection.close()

    def add_image(self, name, image_url):
        results = self.deepsky.find({'$or': [{'object': name}, {'alias': name}]})
        for result in results:
            self.__update__(self.deepsky, 'object', result['object'], 'image', image_url)

    def add_chinese_name(self, id, chinese_name, chinese_alias):
        results = self.deepsky.find({'$or': [{'object': id}, {'alias': id}]})
        for result in results:
            self.__update__(self.deepsky, 'object', result['object'], 'cn_name', chinese_name)
            self.__update__(self.deepsky, 'object', result['object'], 'cn_alias', chinese_alias)

    def add_alias(self, id, alias):
        results = self.deepsky.find({'$or': [{'object': id}, {'alias': id}]})
        for result in results:
            self.__addtoset__(self.deepsky, 'object', result['object'], 'alias', alias)

    def __insert__(self, collection, item):
        if self.debug:
            print "Insert: %s" % item
        else:
            collection.insert(item)

    def __addtoset__(self, collection, id_key, id_val, key, values):
        if self.debug:
            print 'Update: %s: %s add %s' % (id_val, key, values)
        else:
            collection.update(
                {id_key: id_val}, {'$addToSet': {key: {'$each': values}}})

    def __update__(self, collection, id_key, id_val, key, value):
        if self.debug:
            print 'Update: %s: %s add %s' % (id_val, key, value)
        else:
            collection.update({id_key: id_val}, {'$set': {key: value}})


def add_image(filename):
    connector = Connector(debug=False)
    f = open(filename)
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip(' \r\n\t')
        if not line:
            continue
        for name in line.split('.')[0].split('-'):
            connector.add_image(name, image_url_format % line)
    f.close()


def fix_mc(**kwargs):
    connector = Connector(debug=False)
    for i in range(110):
        connector.add_alias('M' + str(i), ['Messier' + str(i)])
        connector.add_alias('C' + str(i), ['Caldwell' + str(i)])


def add_chinese(filename):
    connector = Connector(debug=False)
    f = open(filename)
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip(' \r\n\t')
        if not line:
            continue
        cols = line.split()
        id = cols[0]
        cn_name = cols[1]
        connector.add_chinese_name(id, cn_name, cols[2:])
    f.close()

func_table = {
    'add_image': add_image,
    'add_chinese': add_chinese,
    'fix_mc': fix_mc
}


if __name__ == "__main__":
    func_table[sys.argv[1]](filename=sys.argv[2])
