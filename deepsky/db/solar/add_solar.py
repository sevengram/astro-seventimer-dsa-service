#! /usr/bin/env python2
# -*- coding:utf8 -*-

import urllib
import pymongo
import sys
from bs4 import BeautifulSoup
from util import http

grabber = http.SimpleUrlGrabber()


class Connector(object):

    def __init__(self, debug=True):
        self.connection = pymongo.Connection('localhost', 27017)
        self.datadb = self.connection.astro_data
        self.datadb.authenticate('dsa', 'dsaeboue')
        self.solar = self.datadb.solar
        self.debug = debug

    def __del__(self):
        self.connection.close()

    def add_basic(self, item):
        self.__insert__(self.solar, item)

    def add_image(self, name, image):
        self.__update__(self.solar, 'name', name, 'image', image)

    def add_cnwiki(self, name, wiki):
        self.__update__(self.solar, 'name', name, 'cn_wiki', wiki)

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


def add_basic(filename):
    connector = Connector(debug=False)
    f = open(filename)
    while True:
        line = f.readline()
        if not line:
            break
        if not line.strip(' \r\n\t'):
            continue
        cols = line.split()
        print cols[1]
        chinese = cols[0].decode('utf8')
        cn_wiki = 'http://zh.m.wikipedia.org/zh-cn/%s' % urllib.quote(cols[0])
        wiki_url = 'http://zh.wikipedia.org/zh-cn/%s' % urllib.quote(cols[0])
        article = get_an_article(wiki_url)
        connector.add_basic(
            {'name': cols[1], 'chinese': chinese, 'alias': cols[3:], 'en_wiki': cols[2], 'cn_wiki': cn_wiki, 'article': article})
    f.close()


def add_image(**karg):
    connector = Connector(debug=False)
    for obj in connector.solar.find():
        image_url = 'http://www.mydeepsky.com/image/solar/%s.jpg' % obj['name']
        connector.add_image(obj['name'], image_url)


def fix_wiki(**karg):
    connector = Connector(debug=False)
    for obj in connector.solar.find():
        cn_wiki = 'http://zh.m.wikipedia.org/zh-cn/%s' % urllib.quote(obj['chinese'].encode('utf8'))
        connector.add_cnwiki(obj['name'], cn_wiki)


def add_image(**karg):
    connector = Connector(debug=False)
    for obj in connector.solar.find():
        image_url = 'http://www.mydeepsky.com/image/solar/%s.jpg' % obj['name']
        connector.add_image(obj['name'], image_url)


def get_an_article(url):
    bs = BeautifulSoup(grabber.get(url))
    allps = bs.find(id='mw-content-text').find_all(name=['p', 'h2', 'ul'], recursive=False)
    results = []
    for p in allps:
        para = p.text.strip(' \r\n\t')
        results.append('\n> %s' % para.replace(u'[编辑]', '') if u'[编辑]' in para else para)
    return '\n'.join(filter(lambda a: a != '', results)) + u'\n\n以上资料来自维基百科'


func_table = {
    'add_basic': add_basic,
    'add_image': add_image,
    'fix_wiki': fix_wiki
}

if __name__ == "__main__":
    func_table[sys.argv[1]](filename=sys.argv[2])
