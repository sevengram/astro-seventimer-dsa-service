#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
import datetime
from util import mongo

def main():
    connector = mongo.Connector(debug=False)
    f = open(sys.argv[1])
    connector.set_unique_index('astro_users', sys.argv[2]+'.records', 'object')
    while True:
        line = f.readline()
        if not line: break
        line = line.strip(' \r\n').replace(' ','')
        if not line: continue
        s = line.split('|')
        object_name = s[0]
        if len(s) < 7:
            observing_time = []
        else:
            t = tuple([int(n) for n in s[1:7]])
            observing_time = [datetime.datetime(*t)-datetime.timedelta(hours=8)]
        connector.add_user_record('deepsky', sys.argv[2], object_name, observing_time)

if __name__ == "__main__":
    main()

