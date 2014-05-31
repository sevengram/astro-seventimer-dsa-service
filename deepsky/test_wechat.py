#! /usr/bin/env python2
# -*- coding:utf8 -*-

import unittest
import tornado.httpclient

from util import xmltodict


target_url = 'http://127.0.0.1:33600/service/wechat'

text_req_body = '''<xml><ToUserName><![CDATA[gh_d188e2888313]]></ToUserName>
<FromUserName><![CDATA[owPaGjgfstRME9boM0mE3ewHBcTQ]]></FromUserName>
<CreateTime>1390748270</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[%s]]></Content>
<MsgId>5973218336818590684</MsgId>
</xml>'''

location_req_body = '''<xml><ToUserName><![CDATA[gh_d188e2888313]]></ToUserName>
<FromUserName><![CDATA[owPaGjgfstRME9boM0mE3ewHBcTQ]]></FromUserName>
<CreateTime>1390837425</CreateTime>
<MsgType><![CDATA[location]]></MsgType>
<Location_X>31.310217</Location_X>
<Location_Y>121.543236</Location_Y>
<Scale>16</Scale>
<Label><![CDATA[testLocation]]></Label>
<MsgId>5973601254627866091</MsgId>
</xml>'''

command_fail_msg = u'找不到这个指令哦'


class WechatTestCase(unittest.TestCase):

    def makeRequest(self, raw):
        client = tornado.httpclient.HTTPClient()
        request = tornado.httpclient.HTTPRequest(
            method='POST', body=raw, url=target_url, connect_timeout=10, request_timeout=10)
        return client.fetch(request)

    def testCommandOK(self):
        response = self.makeRequest(text_req_body % '1')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'command')
        self.assertEqual(info['MsgType'], 'text')
        self.assertNotEqual(info['Content'], command_fail_msg)

    def testCommandFail(self):
        response = self.makeRequest(text_req_body % '9')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'command')
        self.assertEqual(info['MsgType'], 'text')
        self.assertEqual(info['Content'], command_fail_msg)

    def testTextWeather(self):
        response = self.makeRequest(text_req_body % u'1徐州')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'weather')
        self.assertEqual(info['MsgType'], 'news')

    def testTextDefault(self):
        response = self.makeRequest(text_req_body % u'啊啊啊啊啊')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'default')
        self.assertEqual(info['MsgType'], 'text')

    def testLocationWeather(self):
        response = self.makeRequest(location_req_body)
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'weather')
        self.assertEqual(info['MsgType'], 'news')
        self.assertEqual(info['Articles']['item']['Title'], 'testLocation')

    def testConstellation(self):
        response = self.makeRequest(text_req_body % u'白羊')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'constellation')
        self.assertEqual(info['MsgType'], 'news')
        self.assertEqual(info['Articles']['item']['Title'], u'白羊座')
        self.assertEqual(info['Articles']['item']['PicUrl'], 'http://www.mydeepsky.com/image/cons/ARI.gif')

    def testDeepsky(self):
        response = self.makeRequest(text_req_body % u'仙女座大星系')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'deepsky')
        self.assertEqual(info['MsgType'], 'news')
        self.assertEqual(info['Articles']['item']['Title'], u'NGC224 - 仙女座大星系')
        self.assertEqual(info['Articles']['item']['PicUrl'], 'http://www.mydeepsky.com/image/deepsky/M31-Gendler.jpg')
        self.assertEqual(info['Articles']['item']['Url'], 'http://zh.m.wikipedia.org/zh-cn/NGC_224')
        print info['Articles']['item']['Description']

    def testSolar(self):
        response = self.makeRequest(text_req_body % u'金星')
        self.assertEqual(response.code, 200)
        info = xmltodict.parse(response.body)['xml']
        self.assertEqual(info['Tag'], 'solar')
        self.assertEqual(info['MsgType'], 'news')
        self.assertEqual(info['Articles']['item']['Title'], u'金星')
        self.assertEqual(info['Articles']['item']['PicUrl'], 'http://www.mydeepsky.com/image/solar/Venus.jpg')
        self.assertEqual(info['Articles']['item']['Url'], 'http://zh.m.wikipedia.org/zh-cn/%E9%87%91%E6%98%9F')


class WechatTestSuite(unittest.TestSuite):

    def __init__(self):
        unittest.TestSuite.__init__(self, map(WechatTestCase, [
            'testCommandOK',
            'testCommandFail',
            'testTextWeather',
            'testLocationWeather',
            'testConstellation',
            'testTextDefault',
            'testDeepsky',
            'testSolar'
        ]))

if __name__ == "__main__":
    unittest.TextTestRunner().run(WechatTestSuite())
