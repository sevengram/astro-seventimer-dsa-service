# -*- coding:utf8 -*-

import re
import urllib
import time
import astro
import xmltodict


def special_decode(text):
    return text.replace('\x00', '<').replace('\x01', '>').replace('\x02', '&')


def special_encode(text):
    return text.replace('<', '\x00').replace('>', '\x01').replace('&', '\x02')


def cdata(text):
    return special_encode('<![CDATA[%s]]>' % text if not text is None else '<![CDATA[]]>')


#
# Build functions
#


def text_response(touser, text, tag):
    response = {'ToUserName': cdata(touser), 'FromUserName': cdata('gh_d188e2888313'), 'CreateTime': int(
        time.time()), 'MsgType': cdata('text'), 'Content': cdata(text), 'Tag': tag}
    result = xmltodict.unparse({'xml': response})
    return special_decode(result[result.index('\n') + 1:])


def seventimer_response(touser, lat, lon, label):
    image_url = 'http://202.127.24.18/v4/bin/astro.php?' + urllib.urlencode(
        {'lon': lon, 'lat': lat, 'lang': 'zh-CN', 'time': int(time.time())})
    response = {'ToUserName': cdata(touser), 'FromUserName': cdata('gh_d188e2888313'), 'CreateTime': int(
        time.time()), 'MsgType': cdata('news'), 'ArticleCount': 1, 'Articles': {'item': []}, 'Tag': 'weather'}
    response['Articles']['item'].append(
        {'Title': cdata(label), 'Description': cdata(u'数据来自晴天钟(7timer.com)'), 'PicUrl': cdata(image_url), 'Url': cdata(image_url)})
    result = xmltodict.unparse({'xml': response})
    return special_decode(result[result.index('\n') + 1:])


def constellation_response(touser, result):
    if result.has_key('common') and result['common']:
        title = '%s (%s)' % (result['chinese'], result['common'])
    else:
        title = result['chinese']
    article = result['article'][:100] + u'...(来自维基百科)'
    response = {'ToUserName': cdata(touser), 'FromUserName': cdata('gh_d188e2888313'), 'CreateTime': int(
        time.time()), 'MsgType': cdata('news'), 'ArticleCount': 1, 'Articles': {'item': []}, 'Tag': 'constellation'}
    response['Articles']['item'].append(
        {'Title': cdata(title), 'Description': cdata(article), 'PicUrl': cdata(result['image']), 'Url': cdata(result['wiki'])})
    result = xmltodict.unparse({'xml': response})
    return special_decode(result[result.index('\n') + 1:])


def solar_response(touser, result, chinese):
    image_url = result['image'] if result.has_key('image') and result['image'] else ''
    target_url = result['cn_wiki'] if chinese else result['en_wiki']
    article = result['article'][:100] + u'...(来自维基百科)'
    response = {'ToUserName': cdata(touser), 'FromUserName': cdata('gh_d188e2888313'), 'CreateTime': int(
        time.time()), 'MsgType': cdata('news'), 'ArticleCount': 1, 'Articles': {'item': []}, 'Tag': 'solar'}
    response['Articles']['item'].append(
        {'Title': cdata(result['chinese']), 'Description': cdata(article), 'PicUrl': cdata(image_url), 'Url': cdata(target_url)})
    result = xmltodict.unparse({'xml': response})
    return special_decode(result[result.index('\n') + 1:])


def deepsky_response(touser, info, chinese):
    response = {'ToUserName': cdata(touser), 'FromUserName': cdata('gh_d188e2888313'), 'CreateTime': int(
        time.time()), 'MsgType': cdata('news'), 'ArticleCount': 1, 'Articles': {'item': []}, 'Tag': 'deepsky'}
    objname = info['object']
    title = objname + ' - %s' % info['cn_name'] if info.has_key('cn_name') and info['cn_name'] else objname
    image_url = info['image'] if info.has_key('image') else ''
    match = re.search('\d', objname)
    if match:
        i = match.start()
        #if chinese:
        if True:
            target_url = 'http://zh.m.wikipedia.org/zh-cn/%s' % '_'.join([objname[:i], objname[i:]])
        else:
            target_url = 'http://en.m.wikipedia.org/wiki/%s' % '_'.join([objname[:i], objname[i:]])
    else:
        target_url = ''
    article = astro.get_description(info)
    response['Articles']['item'].append(
        {'Title': cdata(title), 'Description': cdata(article), 'PicUrl': cdata(image_url), 'Url': cdata(target_url)})
    result = xmltodict.unparse({'xml': response})
    return special_decode(result[result.index('\n') + 1:])
