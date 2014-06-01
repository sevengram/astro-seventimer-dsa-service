#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
from util import mongo

def main():
    isdebug = False
    if len(sys.argv) >= 3 and sys.argv[2] == '-d':
        isdebug = True
    connector = mongo.Connector(debug=isdebug)
    f = open(sys.argv[1])
    line = f.readline()
    while True:
        line = f.readline()
        if not line: break
        line = line.strip(' \r\n\t')
        if not line: continue
        if line == 'SkyObject=BeginObject':
            record = {'CatalogNumber':[], 'CommonName':[]}
        elif line == 'EndObject=SkyObject':
            connector.add_to_ssinfo('deepsky', record)
        else:
            (key, value) = tuple(line.split('='))
            try:
                record[key].append(value)
            except:
                record[key] = value

if __name__ == "__main__":
    main()
