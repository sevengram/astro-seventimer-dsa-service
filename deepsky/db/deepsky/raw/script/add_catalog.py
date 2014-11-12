#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
from util import mongo

def main():
    connector = mongo.Connector(debug=False)
    catalog_name = sys.argv[1]
    f = open('./catalogs/%s' % catalog_name)
    connector.set_unique_index('astro_data', 'catalogs.' + catalog_name, 'object')
    while True:
        line = f.readline()
        if not line: break
        object_name = line.strip(' \r\n').replace(' ','')
        if not object_name: continue
        connector.add_to_catalogs('deepsky', object_name, catalog_name)

if __name__ == "__main__":
    main()
