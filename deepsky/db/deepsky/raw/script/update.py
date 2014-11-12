#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
from bs4 import BeautifulSoup
from util import config, mongo, http, document

def main():    
    settings = config.Settings(sys.argv[1])
    connector = mongo.Connector(debug=settings.debug_mode)
    grabber = http.SimpleUrlGrabber()
    grabber.set_proxy('127.0.0.1:8087')

    filename = r'./data/%s/%s' % (settings.database_name, settings.file_name)
    use_url = hasattr(settings,'url') and settings.url != ''
    f = open(filename)
    if not f.readline().startswith(settings.database_name):
        return
    while True:
        line = f.readline()
        if not line: break
        if not line.strip(' \r\n\t'): continue
        if not use_url:
            connector.update(
                document.DeepskyObject(line, settings).get_info(),
                'deepsky',
                settings.update_keys, 
                settings.overwrite_keys,
                settings.search_mode)
        else:
            con = line.strip(' \r\n')
            print con
            items = BeautifulSoup(grabber.get(settings.url % con)).find_all('table')[7].find_all('tr')[1:]
            defaults = [('type', 'GALCL'), ('con', con)]
            for item in items:
                connector.update(
                    document.DeepskyObject(item,settings,defaults).get_info(),
                    'deepsky',
                    settings.update_keys, 
                    settings.overwrite_keys,
                    settings.search_mode)           
    f.close()

if __name__ == "__main__":
    main()

