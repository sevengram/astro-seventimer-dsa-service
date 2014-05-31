# -*- coding:utf8 -*-

import urllib2

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.79 Safari/537.4'
TIME_OUT = 20

class UrlGrabber(object):
    def __init__(self):
        self.headers = {'User-Agent' : USER_AGENT, 'Accept': 'text/plain', 'Connection': 'Keep-Alive'}
        self.time_out = TIME_OUT
    def get(self, url):
        raise NotImplementedError()

class SimpleUrlGrabber(UrlGrabber):
    def __init__(self):
        super(SimpleUrlGrabber, self).__init__()
        self.proxy = None

    def get(self, url):
        req = urllib2.Request(url, None, self.headers)
        try:
            res = self.proxy.open(req,timeout=self.time_out) if self.proxy else urllib2.urlopen(req, timeout=self.time_out)
            if 200 == res.code:
                return res
            else:
                return None
        except:
            return None

    def set_proxy(self, proxy):
        proxy_handler = urllib2.ProxyHandler({"http" : proxy})
        self.proxy = urllib2.build_opener(proxy_handler)

    def unset_proxy(self):
        self.proxy = None
