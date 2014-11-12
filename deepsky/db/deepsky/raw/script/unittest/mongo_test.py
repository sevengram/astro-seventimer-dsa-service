#! /usr/bin/env python2
# -*- coding:utf8 -*-

import unittest
import sys
sys.path.append('..')

from util import mongo

class ConnectorTestCase(unittest.TestCase):
    def setUp(self):
        f = open('config')
        while True:
            line = f.readline()
            if not line: break
            if not line.strip(' \r\n'): continue
            key_set, raw_value = tuple([v.strip(' []\r\n') for v in line.split('=')])
            setattr(self, key_set, [v.strip(' \'\"') for v in raw_value.split(',')])
        f.close()
        self.client = mongo.Connector(debug=True)

    def tearDown(self):
        pass

    def testUpdate(self):
        item = {'object':'NGC2279', 'mag':19.9, 'size':'test', 'alias':['test1','test2']}
        self.client.update(item, 'deepsky', self.update_keys, self.overwrite_keys)

    def testInsert(self):
        item = {'object':'NGC9999', 'mag':19.9, 'size':'test', 'alias':['test1','test2']}
        self.client.update(item, 'deepsky', self.update_keys, self.overwrite_keys)

class ConnectorTestSuite(unittest.TestSuite):
    def __init__(self):
        super(ConnectorTestSuite, self).__init__(
            map(ConnectorTestCase,('testUpdate','testInsert')))

if __name__ == "__main__":
    unittest.TextTestRunner().run(ConnectorTestSuite())
