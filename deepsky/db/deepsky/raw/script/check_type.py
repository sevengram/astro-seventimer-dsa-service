#! /usr/bin/env python2
# -*- coding:utf8 -*-

import sys

from bs4 import BeautifulSoup
from url_grabber import SimpleURLGrabber

url_format = "http://www.nightskyatlas.com/%sData.jsp?id=%s"
constellations = ['AND','ANT','APS','AQL','AQR','ARA','ARI','AUR','BOO',
                      'CAE','CAM','CAP','CAR','CAS','CEN','CEP','CET','CHA',
                      'CIR','CMA','CMI','CNC','COL','COM','CRA','CRB','CRT',
                      'CRU','CRV','CVN','CYG','DEL','DOR','DRA','EQU','ERI',
                      'FOR','GEM','GRU','HER','HOR','HYA','HYI','IND','LAC',
                      'LEO','LEP','LIB','LMI','LUP','LYN','LYR','MEN','MIC',
                      'MON','MUS','NOR','OCT','OPH','ORI','PAV','PEG','PER',
                      'PHE','PIC','PSA','PSC','PUP','PYX','RET','SCL','SCO',
                      'SCT','SER','SEX','SGE','SGR','TAU','TEL','TRA','TRI',
                      'TUC','UMA','UMI','VEL','VIR','VOL','VUL']

keys = ['object','ra','dec','size_max','size_min','pa','mag','subr','type','class']
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

grabber = SimpleURLGrabber()
catalog = sys.argv[1].lower()

def main():
    for con in constellations:
        url = url_format % (catalog, con)
        print('Processing... %s' % url)
        ic_items = BeautifulSoup(grabber.get_raw_html(url)).find_all('table')[7].find_all('tr')[1:]
        for item in ic_items:
            try:
                values = [i.text.strip() for i in item.find_all('td')]
                if not abbr.has_key(values[-2]):
                    print(values[-2])
                    abbr[values[-2]] = 'OK'
            except:
                print("Fail to process: %s" % item)
    for pair in abbr.items():
        print("%s : %s" % pair)

if __name__ == "__main__":
    main()
