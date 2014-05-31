# -*- coding:utf8 -*-

import MySQLdb
import ConfigParser


class Connector(object):

    def __init__(self, dbname, config_file):
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
        self.usr = config.get(dbname, 'usr')
        self.pwd = config.get(dbname, 'pwd')
        self.dbname = dbname
        self.connect()

    def __del__(self):
        self.connection.close()

    def connect(self):
        self.connection = MySQLdb.connect(
            user=self.usr, passwd=self.pwd, host='localhost', db=self.dbname, charset='utf8')

    def execute(self, query, args):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, args)
        except (AttributeError, MySQLdb.OperationalError):
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query, args)
        finally:
            cursor.close()

    def insert_db(self, table, dic):
        columns = ', '.join(dic.keys())
        placeholders = ', '.join(['%s'] * len(dic))
        request = 'INSERT INTO %s (%s) VALUES (%s)' % (table, columns, placeholders)
        self.execute(request, dic.values())


class SeventimerConnector(Connector):

    def __init__(self, config_file):
        super(SeventimerConnector, self).__init__('seventimer_stat', config_file)

    def add_device(self, dic):
        columns = ', '.join(dic.keys())
        placeholders = ', '.join(['%s'] * len(dic))
        request = "INSERT INTO devices (%s) VALUES (%s) ON DUPLICATE KEY UPDATE version='%s'" % (
            columns, placeholders, dic['version'])
        self.execute(request, dic.values())
