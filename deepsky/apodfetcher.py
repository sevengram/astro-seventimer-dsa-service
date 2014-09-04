#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
import Image
import json
import urllib2
import time
import urllib
import datetime
import tornado.httpclient
import re

from util import httputil
from bs4 import BeautifulSoup
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-l', '--limit',
                  dest='retry_limit',
                  default=10,
                  help='')
parser.add_option('-d', '--picdir',
                  dest='target_dir',
                  help='')
parser.add_option('-t', '--time',
                  dest='retry_time',
                  default=20,
                  help='')
parser.add_option('-s', '--size',
                  dest='pic_width',
                  default=480,
                  help='')

(options, args) = parser.parse_args()

send_url = 'http://127.0.0.1/service/wxmultisend'
upload_url = 'http://127.0.0.1/service/wxupload'
pic_base_url = 'http://www.phys.ncku.edu.tw/~astrolab/mirrors/apod/'
cn_base_url = 'http://www.phys.ncku.edu.tw/~astrolab/mirrors/apod/ap%s.html'
en_base_url = 'http://apod.nasa.gov/apod/ap%s.html'

target_dir = options.target_dir


def replace_blanks(text):
    t = text.strip().replace('\n', '').replace('\r', '').replace('\t', '').replace(u'\uff1b', '; ').replace(
        u'\uff1f', '? ').replace(u'\uff0c', ', ').replace(u'\uff0e', '').replace(u'\uff1a', ': ').replace(
            u'\uff01', '! ').replace(u'\u3002', '. ').replace(u'\u2500', '--').replace('(', ' (').replace(
                ')', ') ').replace(':', ': ')
    return re.sub('\s+', ' ', t)


def compress_image(src, dest, max_width):
    with open(src, 'r') as f1:
        img = Image.open(f1)
        w, h = img.size
        f2 = open(dest, 'w')
        nw = min(max_width, w)
        nh = int(float(nw * h) / w)
        img.resize((nw, nh)).save(f2, 'JPEG', quality=85)
        f2.close()
        f1.close()


def fetch_apod(max_width):
    date = datetime.datetime.now().strftime('%y%m%d')
    cn_url = cn_base_url % date
    en_url = en_base_url % date
    raw = httputil.SimpleUrlGrabber().get(cn_url)
    if raw:
        data = BeautifulSoup(httputil.SimpleUrlGrabber().get(cn_url))
    else:
        print 'no data'
        return None

    try:
        title = replace_blanks(data.find_all('center')[1].find('b').text)
        author = replace_blanks(data.find_all('center')[1].text).replace(title, '').strip()
        article = replace_blanks(
            '\n'.join([p.text for p in data.find('body').findChildren(
                name='p', recursive=False)]).replace(u'\u8aaa\u660e:', ''))
        t = data.find_all('center')[-1].text
        translate = replace_blanks(t[t.find(u'\u7ffb\u8b6f'):])
        picurl = pic_base_url + data.find('center').find_all('a')[-1].get('href')
        f = urllib2.urlopen(picurl)
        dest = target_dir + '%s.%s' % (date, picurl.split('.')[-1])
        with open(dest, 'wb') as target:
            target.write(f.read())
            target.close()
            small_dest = target_dir + '%s_small.jpg' % date
            compress_image(dest, small_dest, max_width)
            return {'filename': small_dest, 'title': title, 'article': article, 'author': author, 'translate': translate, 'cn_url': cn_url, 'en_url': en_url}
        return None
    except AttributeError:
        print 'parse error'
        return None
    except IOError:
        print 'IO error'
        return None
    except urllib2.HTTPError:
        print 'pic url error: ', picurl
        return None


def upload_material(data):
    body = {}
    body['filename'] = data['filename']
    body['title'] = (u'[每日天文一圖] ' + data['title']).encode('utf-8')
    body['content'] = (
        u'<p><strong>%s</strong></p><p><strong>%s</strong></p><p><br/></p><p>%s</p><p><br/></p><p><strong>资料来自:</strong></p><p>%s</p><p>%s</p><p><br/></p><p style="color: rgb(37, 79, 130);"><strong>---------------</strong></p><p style="color: rgb(54, 96, 146);"><strong>欢迎关注邻家天文馆, 这里有什么好玩的呢?</strong></p><p style="color: rgb(71, 113, 162);"><strong>1.从晴天钟获取天气预报</strong></p><p style="color: rgb(89, 129, 178);"><strong>2.查询全天88星座</strong></p><p style="color: rgb(106, 145, 194);"><strong>3.查询超过3万个深空天体</strong></p><p style="color: rgb(124, 162, 210);"><strong>4.解析星空照片</strong></p><p style="color: rgb(141, 179, 226);"><strong>如需详细帮助, 请回复对应数字.</strong></p>' % (
            data['author'], data['translate'], data['article'], data['en_url'], data['cn_url'])).encode('utf-8')
    body['sourceurl'] = data['cn_url']
    body['digest'] = (data['article'][:100] + '...').encode('utf-8')

    client = tornado.httpclient.HTTPClient()
    req = tornado.httpclient.HTTPRequest(
        url=upload_url, method='POST', headers={}, body=urllib.urlencode(body), connect_timeout=60, request_timeout=60)
    res = client.fetch(req)
    if res.code == 200:
        result = json.loads(res.body, encoding='utf-8')
        if result.get('err') == 0:
            return result.get('msg')
    return None


def send_message(mid):
    client = tornado.httpclient.HTTPClient()
    req = tornado.httpclient.HTTPRequest(
        url=send_url, method='POST', headers={}, body=urllib.urlencode({'appmsgid': mid}), connect_timeout=60, request_timeout=60)
    res = client.fetch(req)
    if res.code == 200:
        return json.loads(res.body, encoding='utf-8')
    else:
        return None


if __name__ == "__main__":
    if not target_dir:
        print 'You must specify target_dir by setting --picdir'
        sys.exit(-1)
    count, limit = 0, options.retry_limit
    result = None
    while True:
        print time.ctime(), 'Try to fetch apod...count:', count
        result = fetch_apod(max_width=options.pic_width)
        sys.stdout.flush()
        if result:
            break
        count += 1
        if count > limit:
            break
        else:
            time.sleep(options.retry_time * 60)

    if not result:
        print time.ctime(), 'Fail to fetch apod', count
        sys.stdout.flush()
        sys.exit(-1)

    mid = upload_material(result)
    if not mid:
        print time.ctime(), 'Fail to upload!'
        sys.stdout.flush()
        sys.exit(-1)
    print time.ctime(), 'Upload OK, mid:', mid
    sys.stdout.flush()

    result = send_message(mid)
    if not result:
        print time.ctime(), 'Multisend fail, status code'
    else:
        if result.get('err') == 0:
            print time.ctime(), 'Multisend OK'
        else:
            print time.ctime(), 'Multisend fail, err msg:', result.get('msg')
    sys.stdout.flush()
