# -*- coding:utf8 -*-

import urllib2

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36'

class UrlGrabber(object):
    def __init__(self, time_out):
        self.headers = {'User-Agent' : user_agent, 'Accept': 'text/html', 'Connection': 'Keep-Alive'}
        self.time_out = time_out
    def get(self, url):
        raise NotImplementedError()

class SimpleUrlGrabber(UrlGrabber):
    def __init__(self, time_out = 60):
        super(SimpleUrlGrabber, self).__init__(time_out)

    def get(self, url):
        req = urllib2.Request(url, None, self.headers)
        try:
            res = urllib2.urlopen(req, timeout=self.time_out)
            if 200 == res.code:
                return res
            else:
                return None
        except:
            return None
