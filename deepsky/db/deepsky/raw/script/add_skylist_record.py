#! /usr/bin/env python2
# -*- coding:utf8 -*-

#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
import time
import datetime
from util import mongo

def main():
    connector = mongo.Connector(debug=False)
    f = open(sys.argv[1])
    connector.set_unique_index('astro_users', sys.argv[2]+'.records', 'object')
    line = f.readline()
    while True:
        line = f.readline()
        if not line: break
        line = line.strip(' \r\n\t')
        if not line: continue
        if line == 'SkyObject=BeginObject':
            record = {'CatalogNumber':[], 'CommonName':[]}
        elif line == 'EndObject=SkyObject':
            if record.has_key('DateObserved'):
                t = time.gmtime((float(record['DateObserved'])-2440587.5)*3600*24)
                observing_time = [datetime.datetime(*t[:6])]
                connector.add_skylist_record('deepsky', sys.argv[2], record, observing_time)
        else:
            (key, value) = tuple(line.split('='))
            try:
                record[key].append(value)
            except:
                record[key] = value

if __name__ == "__main__":
    main()


