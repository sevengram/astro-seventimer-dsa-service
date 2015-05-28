# -*- coding:utf8 -*-

import time
import json
import urllib
import datetime

import tornado.gen
import tornado.httpclient
import tornado.web
import ephem


class WeatherHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        lon = self.get_argument('lon')
        lat = self.get_argument('lat')
        client = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest(url="http://202.127.24.18/v4/bin/astro.php?" + urllib.urlencode(
            {'lon': lon, 'lat': lat, 'output': 'json'}), connect_timeout=10, request_timeout=10)
        start_time = time.time()
        response = yield client.fetch(request)
        if response.code == 200:
            body = json.loads(response.body)
            body['solar'] = get_suninfo(
                lon, lat, datetime.datetime.strptime(body['init'], '%Y%m%d%H'), 4)
            end_time = time.time()
            result = {'type': 'service@weather', 'err': 0, 'data': body, 'delay': long((end_time - start_time) * 1000)}
            self.write(result)
            self.finish()
        else:
            self.send_error(response.code)

    def write_error(self, status_code, **kwargs):
        result = {'type': 'service@weather', 'err': status_code, 'data': {}}
        self.write(json.dumps(result))


def get_suninfo(lon, lat, start_time, days):
    result = {'rise_set': [], 'twilight': []}
    sun = ephem.Sun()
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.pressure = 0
    observer.date = start_time
    observer.horizon = '-0:34'
    for i in range(days):
        try:
            next_time = observer.next_rising(sun).datetime()
            result['rise_set'].append(next_time.strftime('%Y%m%d%H%M'))
            observer.date = next_time
        except ephem.NeverUpError, ephem.AlwaysUpError:
            observer.date = observer.date.datetime() + datetime.timedelta(days=1)
    observer.date = start_time
    for i in range(days):
        try:
            next_time = observer.next_setting(sun).datetime()
            result['rise_set'].append(next_time.strftime('%Y%m%d%H%M'))
            observer.date = next_time
        except ephem.NeverUpError, ephem.AlwaysUpError:
            observer.date = observer.date.datetime() + datetime.timedelta(days=1)
    observer.date = start_time
    observer.horizon = '-18'
    for i in range(days):
        try:
            next_time = observer.next_rising(sun).datetime()
            result['twilight'].append(next_time.strftime('%Y%m%d%H%M'))
            observer.date = next_time
        except ephem.NeverUpError, ephem.AlwaysUpError:
            observer.date = observer.date.datetime() + datetime.timedelta(days=1)
    observer.date = start_time
    for i in range(days):
        try:
            next_time = observer.next_setting(sun).datetime()
            result['twilight'].append(next_time.strftime('%Y%m%d%H%M'))
            observer.date = next_time
        except ephem.NeverUpError, ephem.AlwaysUpError:
            observer.date = observer.date.datetime() + datetime.timedelta(days=1)
    return result
