#! /usr/bin/env python2
# -*- coding:utf8 -*-

import unittest
import sys
sys.path.append('..')

from bs4 import BeautifulSoup
from util import http

class GrabberTestCase(unittest.TestCase):
    def setUp(self):
        self.grabber = http.SimpleUrlGrabber()

    def tearDown(self):
        pass

    def testGet(self):
        self.grabber.unset_proxy()
        result = self.grabber.get('http://www.baidu.com')
        self.assertEqual(result.code, 200)
        self.assertTrue(BeautifulSoup(result).title.text.startswith(u'百度'))
        self.assertEqual(self.grabber.get('http://www.facebook.com'), None)

    def testProxy(self):
        self.grabber.set_proxy('127.0.0.1:8087')
        result = self.grabber.get('http://www.youtube.com')
        self.assertEqual(result.code, 200)
        self.assertTrue(BeautifulSoup(result).title.text.startswith(u'YouTube'))
        self.grabber.unset_proxy()
        self.assertEqual(self.grabber.get('http://www.facebook.com'), None)

class GrabberTestSuite(unittest.TestSuite):
    def __init__(self):
        super(GrabberTestSuite, self).__init__(
            map(GrabberTestCase,('testGet','testProxy')))

if __name__ == "__main__":
    unittest.TextTestRunner().run(GrabberTestSuite())
