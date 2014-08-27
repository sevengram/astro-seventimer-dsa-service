# -*- coding:utf8 -*-

from util import mysql

class SeventimerDealer(object):

    def __init__(self, config_file):
        self.conn = mysql.SeventimerConnector(config_file)

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


