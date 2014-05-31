#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys
from util import config, mongo, document

def main():    
    settings = config.Settings(sys.argv[1])
    connector = mongo.Connector(debug=settings.debug_mode)
    filename = r'%s' % settings.file_name
    f = open(filename)
    if not f.readline().startswith(settings.database_name):
        return
    while True:
        line = f.readline()
        if not line: break
        if not line.strip(' \r\n\t'): continue
        connector.update(
            document.DeepskyObject(line, settings).get_info(),
            'deepsky',
            settings.update_keys, 
            settings.overwrite_keys,
            settings.search_mode)
    f.close()

if __name__ == "__main__":
    main()
