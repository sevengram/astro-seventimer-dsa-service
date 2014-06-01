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
        self.constellation = self.datadb.constellation
        self.debug = debug

    def __del__(self):
        self.connection.close()

    def add_basic(self, item):
        self.__insert__(self.constellation, item)

    def add_extra_names(self, abbr, names):
        self.__addtoset__(self.constellation, 'abbr', abbr, 'alias', names)

    def add_gen(self, abbr, gen):
        self.__update__(self.constellation, 'abbr', abbr, 'gen', gen)

    def add_article(self, abbr, article):
        self.__update__(self.constellation, 'abbr', abbr, 'article', article)

    def add_wiki(self, abbr, wiki):
        self.__update__(self.constellation, 'abbr', abbr, 'wiki', wiki)

    def add_image(self, abbr, image):
        self.__update__(self.constellation, 'abbr', abbr, 'image', image)

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
        chinese = cols[0].decode('utf8')
        connector.add_basic(
            {'abbr': cols[1], 'chinese': chinese, 'alias': [chinese[:-1]], 'full': cols[2].replace('_', ' ')})
    f.close()


def add_extra(filename):
    connector = Connector(debug=False)
    f = open(filename)
    while True:
        line = f.readline()
        if not line:
            break
        if not line.strip(' \r\n\t'):
            continue
        cols = line.split()
        chinese = cols[1].decode('utf8')
        connector.add_extra_names(cols[0], [chinese, chinese[:-1]])
    f.close()


def add_gen(filename):
    connector = Connector(debug=False)
    f = open(filename)
    while True:
        line = f.readline()
        if not line:
            break
        if not line.strip(' \r\n\t'):
            continue
        cols = line.split()
        connector.add_gen(cols[0].upper(), cols[1].replace('_', ' '))
    f.close()


def add_article(**karg):
    connector = Connector(debug=False)
    #for obj in connector.constellation.find():
    for obj in connector.constellation.find({'abbr':{'$in':['QUA','ARG']}}):
        article_url = 'http://zh.wikipedia.org/zh-cn/%s' % urllib.quote(obj['chinese'].encode('utf8'))
        wiki_url = 'http://zh.m.wikipedia.org/zh-cn/%s' % urllib.quote(obj['chinese'].encode('utf8'))
        article = get_an_article(article_url)
        connector.add_article(obj['abbr'], article)
        connector.add_wiki(obj['abbr'], wiki_url)

def add_image(**karg):
    connector = Connector(debug=False)
    for obj in connector.constellation.find():
        image_url = 'http://www.mydeepsky.com/image/cons/%s.gif' % obj['abbr']
        connector.add_image(obj['abbr'], image_url)


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
    'add_extra': add_extra,
    'add_article': add_article,
    'add_gen': add_gen,
    'add_image': add_image
}

if __name__ == "__main__":
    func_table[sys.argv[1]](filename=sys.argv[2])
