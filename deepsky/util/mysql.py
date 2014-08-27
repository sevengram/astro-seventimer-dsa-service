# -*- coding:utf8 -*-

import MySQLdb

from MySQLdb import cursors


class Connector(object):

    def __init__(self, dbname):
        self.usr = 'dsa'
        self.pwd = 'Dsaeboue123'
        self.dbname = dbname
        self.connect()

    def __del__(self):
        self.connection.close()

    def connect(self):
        self.connection = MySQLdb.connect(
            user=self.usr, passwd=self.pwd, host='eridanus.mysql.rds.aliyuncs.com', db=self.dbname, charset='utf8')

    def execute(self, query, args, usedict=False, cursorclass=MySQLdb.cursors.DictCursor):
        cursor = self.connection.cursor(cursorclass)
        rs = None
        try:
            cursor.execute(query, args)
            rs = cursor.fetchone()
        except (AttributeError, MySQLdb.OperationalError):
            self.connection.close()
            self.connect()
            cursor = self.connection.cursor(cursorclass)
            cursor.execute(query, args)
            rs = cursor.fetchone()
        finally:
            cursor.close()
            return rs

    def insert_db(self, table, dic):
        columns = ', '.join(dic.keys())
        placeholders = ', '.join(['%s'] * len(dic))
        request = 'INSERT INTO %s (%s) VALUES (%s)' % (
            table, columns, placeholders)
        self.execute(request, dic.values())

    def replace_db(self, table, dic):
        columns = ', '.join(dic.keys())
        placeholders = ', '.join(['%s'] * len(dic))
        updates = ', '.join(map(lambda n: n + ' = %s', dic.keys()))
        request = 'INSERT INTO %s (%s) VALUES (%s) ON DUPLICATE KEY UPDATE %s' % (
            table, columns, placeholders, updates)
        self.execute(request, dic.values() * 2)


class WechatConnector(Connector):

    def __init__(self):
        super(WechatConnector, self).__init__('wechat')

    def add_user(self, dic):
        self.replace_db('users', dic)

    def add_location(self, dic):
        self.insert_db('location', dic)

    def add_feedback(self, dic):
        self.insert_db('feedback', dic)

    def get_fakeid(self, uid):
        request = 'SELECT fakeid FROM users WHERE uid = %s AND fakeid !=""'
        return self.execute(request, [uid])

    def get_location(self, query):
        request = 'SELECT * FROM location WHERE query = %s'
        return self.execute(request, [query])

    def get_lastquery(self, uid):
        request = 'SELECT * FROM users WHERE uid = %s'
        return self.execute(request, [uid])
