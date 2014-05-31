# -*- coding:utf8 -*-

import re
import urllib
import sys
import json
import hashlib
import tornado.web
import tornado.gen
import tornado.httpclient

from collections import defaultdict

from util import xmltodict
from util import mysql
from util import xmlcdata
from util import motordb
from util.consts import *

type_dict = defaultdict(lambda: ['default'], {
    'location': ['weather1', 'default'],
    'text': ['command', 'constellation', 'deepsky', 'solar', 'weather1', 'weather2', 'default'],
    'event': ['welcome']
})

mongo_conn = motordb.Connector(debug=False)
mysql_conn = mysql.WechatConnector()

#
# Is functions
#


def is_weather1(request):
    if request['MsgType'] == 'location':
        return True
    elif request['MsgType'] == 'text':
        content = request['Content']
        return len(content) >= 2 and contains(content, loc_keys_l1)
    else:
        return False


def is_weather2(request):
    if request['MsgType'] == 'text':
        content = request['Content']
        return len(content) >= 2 and (contains(content, loc_keys_l2) or mysql_conn.get_location(content))
    else:
        return False

#
# Process functions
#


@tornado.gen.coroutine
def process_weather1(request, **kwargs):
    if is_weather1(request):
        response = yield process_weather(request)
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_weather2(request, **kwargs):
    if is_weather2(request):
        response = yield process_weather(request)
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_weather(request, **kwargs):
    if request['MsgType'] == 'location':
        response = xmlcdata.seventimer_response(
            request['FromUserName'], request['Location_X'], request['Location_Y'], request['Label'])
        raise tornado.gen.Return(response)
    else:
        query = request['Content']
        if query[0] < '9' and query[0] > '0':
            query = query[1:]
        location = mysql_conn.get_location(query)
        if not location:
            location = yield get_location(query)
            if location:
                mysql_conn.add_location(location)
        if location:
            response = xmlcdata.seventimer_response(
                request['FromUserName'], location['latitude'], location['longitude'], location['address'])
            raise tornado.gen.Return(response)
        else:
            raise tornado.gen.Return(None)


@tornado.gen.coroutine
def get_location(query):
    query = query.encode('utf8')
    client = tornado.httpclient.AsyncHTTPClient()
    map_url = "http://maps.googleapis.com/maps/api/geocode/json?" + urllib.urlencode(
        {'address': query, 'sensor': 'false', 'language': 'zh-CN'})
    locreq = tornado.httpclient.HTTPRequest(url=map_url, connect_timeout=10, request_timeout=10)
    locres = yield client.fetch(locreq)
    if locres.code == 200:
        try:
            report = json.loads(locres.body)
            if report['status'] == 'OK':
                result = report['results'][0]
                label = result['formatted_address']
                lng = result['geometry']['location']['lng']
                lat = result['geometry']['location']['lat']
                raise tornado.gen.Return({'query': query, 'address': label, 'longitude': lng, 'latitude': lat})
            else:
                print 'process_weather:%s Fail => report[status] != OK' % query
                raise tornado.gen.Return(None)
        except KeyError, e:
            print 'process_weather:%s Fail KeyError' % query
            raise tornado.gen.Return(None)
    else:
        print 'process_weather:%s Fail => locres.code == %d' % (query, locres.code)
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_default(request, **kwargs):
    if request.has_key('Content') and request['Content']:
        message = default_format % request['Content']
    else:
        message = default_response
    raise tornado.gen.Return(
        xmlcdata.text_response(request['FromUserName'], message, 'default'))


@tornado.gen.coroutine
def process_welcome(request, **kwargs):
    raise tornado.gen.Return(
        xmlcdata.text_response(request['FromUserName'], welcome_direction, 'welcome'))


@tornado.gen.coroutine
def process_command(request, **kwargs):
    cmd = request['Content']
    if text_commands.has_key(cmd):
        cmd = text_commands[cmd]
    if len(cmd) == 1 and cmd <= '9' and cmd >= '0':
        response = None
        history = mysql_conn.get_lastquery(request['FromUserName'])
        if history and not history['last_status'] and history['last_query']:
            if cmd == '1':
                response = yield process_weather({'Content': history['last_query'], 'MsgType': 'text', 'FromUserName': request['FromUserName']})
            if not response:
                mysql_conn.add_feedback({'uid': request['FromUserName'], 'query': history['last_query'], 'type': cmd})
        if response:
            raise tornado.gen.Return(response)
        else:
            raise tornado.gen.Return(
                xmlcdata.text_response(request['FromUserName'], command_dicts[cmd], 'command'))
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_constellation(request, **kwargs):
    query = request['Content']
    result = yield mongo_conn.find_constellation(query)
    if result:
        response = xmlcdata.constellation_response(request['FromUserName'], result)
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_solar(request, **kwargs):
    query = request['Content']
    result = yield mongo_conn.find_solar(query)
    if result:
        response = xmlcdata.solar_response(request['FromUserName'], result, is_chinese(query[0]))
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_deepsky(request, **kwargs):
    query = request['Content']
    match = re.search('\d', query)
    usetitle = match and query[:match.start()].strip().lower() in [
        'messier', 'caldwell', 'abell', 'stock', 'berk', 'arp', 'cr', 'tr', 'sh']
    query = query.title() if len(query.split()) > 1 or usetitle else query.upper()
    querys = [query, query.replace(' ', '')] if ' ' in query else [query]
    for q in querys:
        result = yield mongo_conn.find_deepsky(q)
        if result:
            raise tornado.gen.Return(xmlcdata.deepsky_response(request['FromUserName'], result, is_chinese(query[0])))
    raise tornado.gen.Return(None)


process_dict = {
    'constellation': process_constellation,
    'command': process_command,
    'weather1': process_weather1,
    'weather2': process_weather2,
    'deepsky': process_deepsky,
    'solar': process_solar,
    'default': process_default,
    'welcome': process_welcome
}


class WechatHandler(tornado.web.RequestHandler):

    def get(self):
        if self.check_signature():
            self.write(self.get_argument('echostr'))

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        req = xmltodict.parse(self.request.body)['xml']
        res = ''
        processed = False
        for p in type_dict[req['MsgType']]:
            res = yield process_dict[p](request=req, body=self.request.body)
            if res:
                processed = (p != 'default')
                break
        self.write(res)
        self.finish()
        last_query = req['Content'] if req.has_key('Content') and req['Content'] else ''
        mysql_conn.add_user({'uid': req['FromUserName'], 'last_query': last_query, 'last_status': processed})
        sys.stdout.flush()

    def check_signature(self):
        arr = ['ilovedeepsky', self.get_argument(
            'timestamp'), self.get_argument('nonce')]
        arr.sort()
        return hashlib.sha1(''.join(arr)).hexdigest() == self.get_argument('signature')


#
# Utils functions
#


def contains(source, group):
    for word in group:
        if word in source:
            return True
    return False


def is_chinese(uchar):
    return uchar >= u'\u4e00' and uchar <= u'\u9fa5'
