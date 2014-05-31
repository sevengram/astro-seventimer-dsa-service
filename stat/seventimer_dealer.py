# -*- coding:utf8 -*-

import ConfigParser

from util import mysql

class SeventimerDealer(object):

    def __init__(self, config_file):
        self.conn = mysql.SeventimerConnector(config_file)
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
        version = config.get('update_info', 'version')
        rev = config.getint('update_info', 'rev')
        url = config.get('update_info', 'url')
        message = config.get('update_info', 'message')
        level = config.getint('update_info', 'level')
        self.update_info = {'version':version, 'rev':rev, 'level':level, 'url':url, 'message':message}

    def __del__(self):
        del self.conn

    def add_device(self, dic, ip):
        self.conn.add_device(dic)

    def start_app(self, dic, ip):
        dic['ip'] = ip
        self.conn.insert_db('start_app', dic)

    def location_stat(self, dic, ip):
        dic['ip'] = ip
        self.conn.insert_db('location_service', dic)

    def satellite_stat(self, dic, ip):
        dic['ip'] = ip
        self.conn.insert_db('satellite_service', dic)

    def weather_stat(self, dic, ip):
        dic['ip'] = ip
        self.conn.insert_db('weather_service', dic)


