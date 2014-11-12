#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
import pymongo

def main():
    catalog = sys.argv[1]
    connection = pymongo.Connection('localhost', 27017)
    datadb = connection.astro_data
    items = getattr(datadb.catalogs, catalog)

    out = open(catalog+'.skylist','w')
    out.write("SkySafariObservingListVersion=3.0\n")
    ssinfo = datadb.ssinfo
    for item in items.find():
        try:
            record = datadb.dereference(item['data'])
            result = ssinfo.find_one({'object':record['object']})
            if not result:
                result = ssinfo.find_one({'alias':record['object']})
            if not result:
                for alias in record['alias']:
                    result = ssinfo.find_one({'object':alias})
                    if not result:
                        result = ssinfo.find_one({'alias':alias})
                    if result != None:
                        break
            r = result['skysafari_info']
            out.write("SkyObject=BeginObject\n")
            out.write('ObjectID=%s\n' % r['ObjectID'])
            for cn in r['CommonName']:
                out.write('CommonName=%s\n' % cn)
            for cn in r['CatalogNumber']:
                out.write('CatalogNumber=%s\n' % cn)
            out.write("EndObject=SkyObject\n")
        except Exception, e:
            print('no ssinfo %s' % record)
            continue

if __name__ == "__main__":
    main()
