# -*- coding:utf8 -*-

import re
import urllib
import sys
import json
import hashlib
import tornado.web
import tornado.gen
import tornado.httpclient
import tornado.curl_httpclient

from collections import defaultdict

from util import xmltodict
from util import mysql
from util import xmlcdata
from util import motordb
from util import consts

type_dict = defaultdict(lambda: ['default'], {
    'image': ['astrometry'],
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
        return len(content) >= 2 and contains(content, consts.loc_keys_l1)
    else:
        return False


def is_weather2(request):
    if request['MsgType'] == 'text':
        content = request['Content']
        return len(content) >= 2 and (contains(content, consts.loc_keys_l2) or mysql_conn.get_location(content))
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
    query = query.encode('utf-8')
    client = tornado.curl_httpclient.CurlAsyncHTTPClient()
    map_url = "http://maps.googleapis.com/maps/api/geocode/json?" + urllib.urlencode(
        {'address': query, 'sensor': 'false', 'language': 'zh-CN'})
    locreq = tornado.httpclient.HTTPRequest(
        url=map_url, connect_timeout=20, proxy_host='192.110.165.49', proxy_port=8180, request_timeout=20)
    locres = yield client.fetch(locreq)
    if locres.code == 200:
        try:
            report = json.loads(locres.body)
            if report['status'] == 'OK':
                result = report['results'][0]
                label = result['formatted_address']
                lng = result['geometry']['location']['lng']
                lat = result['geometry']['location']['lat']
                raise tornado.gen.Return(
                    {'query': query, 'address': label, 'longitude': lng, 'latitude': lat})
            else:
                print 'process_weather:%s Fail => report[status] != OK' % query
                raise tornado.gen.Return(None)
        except KeyError:
            print 'process_weather:%s Fail KeyError' % query
            raise tornado.gen.Return(None)
    else:
        print 'process_weather:%s Fail => locres.code == %d' % (query, locres.code)
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_default(request, **kwargs):
    if request.has_key('Content') and request['Content']:
        message = consts.default_format % request['Content']
    else:
        message = consts.default_response
    raise tornado.gen.Return(
        xmlcdata.text_response(request['FromUserName'], message, 'default'))


@tornado.gen.coroutine
def process_welcome(request, **kwargs):
    raise tornado.gen.Return(
        xmlcdata.text_response(request['FromUserName'], consts.welcome_direction, 'welcome'))


@tornado.gen.coroutine
def process_command(request, **kwargs):
    cmd = request['Content']
    if consts.text_commands.has_key(cmd):
        cmd = consts.text_commands[cmd]
    if len(cmd) == 1 and cmd <= '9' and cmd >= '0':
        response = None
        history = mysql_conn.get_lastquery(request['FromUserName'])
        if history and not history['last_status'] and history['last_query']:
            if cmd == '1':
                response = yield process_weather({'Content': history['last_query'], 'MsgType': 'text', 'FromUserName': request['FromUserName']})
            if not response:
                mysql_conn.add_feedback(
                    {'uid': request['FromUserName'], 'query': history['last_query'], 'type': cmd})
        if response:
            raise tornado.gen.Return(response)
        else:
            raise tornado.gen.Return(
                xmlcdata.text_response(request['FromUserName'], consts.command_dicts[cmd], 'command'))
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_constellation(request, **kwargs):
    query = request['Content']
    result = yield mongo_conn.find_constellation(query)
    if result:
        response = xmlcdata.constellation_response(
            request['FromUserName'], result)
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_solar(request, **kwargs):
    query = request['Content']
    result = yield mongo_conn.find_solar(query)
    if result:
        response = xmlcdata.solar_response(
            request['FromUserName'], result, is_chinese(query[0]))
        raise tornado.gen.Return(response)
    else:
        raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_deepsky(request, **kwargs):
    query = request['Content']
    match = re.search('\d', query)
    usetitle = match and query[:match.start()].strip().lower() in [
        'messier', 'caldwell', 'abell', 'stock', 'berk', 'arp', 'cr', 'tr', 'sh']
    query = query.title() if len(
        query.split()) > 1 or usetitle else query.upper()
    querys = [query, query.replace(' ', '')] if ' ' in query else [query]
    for q in querys:
        result = yield mongo_conn.find_deepsky(q)
        if result:
            raise tornado.gen.Return(xmlcdata.deepsky_response(
                request['FromUserName'], result, is_chinese(query[0])))
    raise tornado.gen.Return(None)


@tornado.gen.coroutine
def process_astrometry(request, **kwargs):
    server_url = 'http://127.0.0.1:33900'
    notify_url = 'http://127.0.0.1/service/wxmessage'
    client = tornado.httpclient.AsyncHTTPClient()
    userinfo = json.dumps({'uid': request['FromUserName'], 'timestamp': long(
        request['CreateTime']), "content": request.get('Content'), "type": request['MsgType']})
    body = urllib.urlencode(
        {'pic_url': request['PicUrl'], 'notify_url': notify_url, 'userinfo': userinfo})
    req = tornado.httpclient.HTTPRequest(
        url=server_url, method='POST', headers={}, body=body, connect_timeout=20, request_timeout=20)
    response = yield client.fetch(req)
    if response.code == 200:
        raise tornado.gen.Return(
            xmlcdata.text_response(request['FromUserName'], 'wait', 'default'))
    else:
        raise tornado.gen.Return(
            xmlcdata.text_response(request['FromUserName'], 'error', 'default'))


process_dict = {
    'constellation': process_constellation,
    'command': process_command,
    'weather1': process_weather1,
    'weather2': process_weather2,
    'deepsky': process_deepsky,
    'solar': process_solar,
    'default': process_default,
    'welcome': process_welcome,
    'astrometry': process_astrometry
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

        # save last query
        last_query = req.get('Content')
        openid = req['FromUserName']
        mysql_conn.add_user(
            {'uid': openid, 'last_query': last_query, 'last_status': processed})

        # bind fakeid
        if req['MsgType'] in ['text', 'location', 'image']:
            if not mysql_conn.get_fakeid(openid):
                userinfo = json.dumps(
                    {'uid': openid, 'timestamp': long(req['CreateTime']), "content": last_query, "type": req['MsgType']})
                client = tornado.httpclient.AsyncHTTPClient()
                req = tornado.httpclient.HTTPRequest(
                    url='http://127.0.0.1/service/wxuser?' +
                        urllib.urlencode({'cached': 0, 'userinfo': userinfo}),
                    method='GET', headers={}, connect_timeout=30, request_timeout=120)
                yield client.fetch(req)

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
