# -*- coding:utf8 -*-

import re
import bs4
from config import Settings

size_keys = ['size','size_max','size_min']
mag_keys = ['mag', 'brstr','subr']
float_keys = ['redshift']
int_keys = ['pa','nsts']
nospace_keys = ['object','size','size_max','size_min']
onespace_keys = ['class','notes','ngc_descr','type','alias']
lower_keys = []
upper_keys = ['con']

abbr = {'open cluster':'OPNCL',
         'emission nebula':'BRTNB',
         'reflection nebula':'BRTNB',
         'elliptic galaxy':'GALXY',
         'barred spiral galaxy':'GALXY',
         'spiral galaxy':'GALXY',
         'compact galaxy':'GALXY',
         'peculiar galaxy':'GALXY',
         'irregular galaxy':'GALXY',
         'globular cluster':'GLOCL',
         'planetary nebula':'PLNNB',
         'galaxy':'GALXY',
         'dwarf galaxy':'GALXY',
         'part of galaxy':'GALXY',
         'galactic nebula or SNR':'SNREM',
         'dark nebula' : 'DRKNB'}

class DeepskyObject(object):
    def __init__(self, line, settings, defaults = []):
        self.settings = settings
        sep = self.settings.key_sep
        if isinstance(line, bs4.element.Tag):
            values = [i.text.strip() for i in line.find_all(sep)]
        else:
            values = [i.strip() for i in line.rstrip('\r\n').strip(sep).split(sep)]
        self.d = dict(zip(self.settings.read_keys, values))
        for key,value in defaults:
            self.d[key] = value
        self.fix_value()        
        self.fix_name()
        self.fix_alias()
        self.fix_type()
        self.update_size()
        self.update_ra_dec()
        self.clean()

    def get_info(self):
        return self.d

    def has(self, key):
        return self.d.has_key(key)

    def get(self, key):
        if not self.has(key):
            return None
        else:
            return self.d[key]

    def fix_name(self):
        p = re.compile(r'^[-\d\s\.]+[a-zA-Z]{0,1}$')
        if self.has('object'):
            name = self.get('object')
            if p.match(name):
                name = self.settings.default_label + name.lstrip('0').replace(' ','')
            if name.startswith('MCG'):
                name = name.replace('-00','-').replace('-0','-')
                if not name.startswith('MCG-') and not name.startswith('MCG+'):
                    name = name.replace('MCG','MCG+')
            if name.startswith('UGC') and name.endswith('A'):
                name = name.replace('UGC','UGCA')[:-1]
            self.d['object'] = name

    def fix_type(self):
        if self.has('type') and abbr.has_key(self.get('type')):
            self.d['type'] = abbr[self.get('type')]

    def fix_alias(self):
        p = re.compile(r'^[-\d\s\.]+[a-zA-Z]{0,1}$')
        l = re.compile(r'[a-z]')
        if self.has('alias'):
            if not isinstance(self.get('alias'), list):
                self.d['alias'] = [v.strip() for v in self.get('alias').split(self.settings.alias_sep)]
            alias = []
            for name in self.get('alias'):
                if name == '':
                    continue
               # if l.search(name) and not name.startswith(
               #     'Mel') and not name.startswith(
               #     'Arp') and not name.startswith(
               #     'Abell') and not name.startswith(
               #     'Sh') and not name.startswith(
               #     'Mrk') and not name.startswith(
               #     'Ced') and not name.startswith(
               #     'Berk'):
               #     continue
                if p.match(name):
                    name = self.settings.alias_label + name.lstrip('0').replace(' ','')
                if name.startswith('MCG'):
                    name = name.replace('-00','-').replace('-0','-')
                    if not name.startswith('MCG-') and not name.startswith('MCG+'):
                        name = name.replace('MCG','MCG+')
                if name.startswith('UGC') and name.endswith('A'):
                    name = name.replace('UGC','UGCA')[:-1]
                alias.append(name)
            self.d['alias'] = alias

    def fix_value(self):
        s = re.compile(r'\s+')
        p = re.compile(u'[hms\'\"\xb4\xb0]')
        for key in self.d:
            if key in mag_keys:
                self.d[key] = float(self.get(key)) if self.get(key) != '' else 99.9
            elif key in float_keys and self.get(key) != '':
                self.d[key] = float(self.get(key))
            elif key in int_keys and self.get(key) != '':
                self.d[key] = int(p.sub('',self.get(key)))
            if key in nospace_keys:
                self.d[key] = self.get(key).replace(' ','')
            elif key in onespace_keys:
                self.d[key] = s.sub(' ', self.get(key))
            if key in upper_keys:
                self.d[key] = self.get(key).upper()
            elif key in lower_keys:
                self.d[key] = self.get(key).lower()

    def update_size(self):
        unit = self.settings.size_unit
        size = ''
        for key in size_keys:
            if self.has(key) and self.get(key) != '':
                self.d[key] = self.get(key).replace(u'\xb0','d').replace(u'\xb4','m').replace(
                    '"','s').lower().strip('x')
                if self.d[key][-1] not in 'dmsr':
                    self.d[key] += unit
                index = self.get(key).find('x')
                if index > 0 and self.get(key)[index-1] not in 'dmsr':
                    self.d[key] = self.get(key).replace('x',unit+'x')
                size += ' ' + self.get(key)
        self.d['size'] = size.strip().replace(' ','x')

    # Throw IndexError
    def update_ra_dec(self):
        if not self.has('ra') or not self.has('dec'):
            return
        p = re.compile(u'[hms\'\"\xb4\xb0]')
        s = re.compile(r'\s+')
        self.d['ra'] = s.sub(' ',p.sub(' ',self.get('ra'))).strip()
        self.d['dec'] = s.sub(' ',p.sub(' ',self.get('dec'))).replace('+ ','+').replace('- ','-').strip()
        try:
            ra = [float(n) for n in self.get('ra').split()]
            dec = [float(n) for n in self.get('dec').split()]
            self.d['ra_value'] = ra[0] + ra[1]/60.0
            self.d['dec_value'] = dec[0]-dec[1]/60.0 if self.get('dec')[0]=='-' else dec[0]+dec[1]/60.0
            if len(ra) > 2: 
                self.d['ra_value'] += ra[2]/3600.0
            if len(dec) > 2:
                if self.get('dec')[0]=='-':
                    self.d['dec_value'] -= dec[2]/3600.0
                else:
                    self.d['dec_value'] += dec[2]/3600.0
        except IndexError:
            raise IndexError('Invalid - RA: %s Dec: %s' % (self.get('ra'), self.get('dec')))

    def clean(self):
        del_keys = []
        for key in self.d:
            if key in self.settings.unused_keys:
               del_keys.append(key)
            elif key not in self.settings.essential_keys:
                if not self.get(key):
                    del_keys.append(key)
                elif key in mag_keys and self.get(key) == 99.9:
                    del_keys.append(key)
                elif isinstance(self.get(key),list) and len(self.get(key)) == 1 and not self.get(key)[0]:
                    del_keys.append(key)
        for key in del_keys:
            del self.d[key]


