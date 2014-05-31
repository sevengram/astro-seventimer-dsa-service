# -*- coding:utf8 -*-

class Settings(object):
     def __init__(self, config_file):
         f = open(config_file)
         while True:
             line = f.readline()
             if not line: break
             if not line.strip(' \r\n'): continue
             l = line.find('=')
             keyset = line[0:l].strip(' \r\n')
             raw_value = line[l+1:].strip(' \r\n')
             if raw_value[0]=='[':
                setattr(self, keyset, [v.strip(' \'\"[]') for v in raw_value.split(',')])
             elif raw_value[0] == '\'':
                setattr(self, keyset, raw_value.strip(' \''))
             elif raw_value.lower() == 'true':
                setattr(self, keyset, True)
             elif raw_value.lower() == 'false':
                setattr(self, keyset, False)
             else:
                setattr(self, keyset, int(raw_value))
         f.close()
