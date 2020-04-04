# -*- coding: utf-8 -*-
import os
import sys
import json
import pymysql

from login.account import account

class dealRecordDBHelper:
    
    def __init__(self):
        # 取用户名密码
        self.account = account()
        # 打开数据库
        self.ip_address = ''
        self.sql_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', 'note']
        if sys.platform.startswith('win'):
            self.ip_address = '112.125.25.230'
        elif sys.platform.startswith('linux'):
            self.ip_address = '127.0.0.1'
    
    ################################################
    # COMMON
    ################################################
    # 连接数据库
    def connect(self):
        return pymysql.connect(self.ip_address, self.account.user, self.account.password, 'deal_record')

    ################################################
    # CREATE
    ################################################

    # 创建基础信息表
    def createDealRecordTableIfNeeded(self):
        sql = """
        CREATE TABLE `klq` (
            `id` INT(11) NULL DEFAULT NULL,
            `date` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `code` VARCHAR(6) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `name` VARCHAR(30) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `dealType` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `nav_unit` DECIMAL(10,4) NULL DEFAULT NULL,
            `nav_acc` DECIMAL(10,4) NULL DEFAULT NULL,
            `volume` DECIMAL(10,2) NULL DEFAULT NULL,
            `dealMoney` DECIMAL(10,2) NULL DEFAULT NULL,
            `fee` DECIMAL(10,2) NULL DEFAULT NULL,
            `occurMoney` DECIMAL(10,2) NULL DEFAULT NULL,
            `account` VARCHAR(20) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category1` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category2` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category3` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `categoryId` INT(11) NULL DEFAULT NULL,
            `note` VARCHAR(200) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            UNIQUE INDEX `id` (`id`)
        )
        COMMENT='康力泉的金融市场成交全记录'
        COLLATE='utf8_unicode_ci'
        ENGINE=InnoDB
        ;
        """
        print(sql)
        db = self.connect()
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
        except Exception as e:
            # 表存在就回滚操作
            db.rollback()
            print(e)
        finally:
            cursor.close()
            db.close()

    ################################################
    # SELECT
    ################################################

    # 返回特定条件的所有成交记录
    def selectAllRecordsOfCode(self, tablename = 'klq', code = '', account = '华泰'):
        if tablename != 'klq':
            tablename = 'parents'
        if len(code) <= 0:
            print('[ERROR] 代码错误：{0}'.format(code))
            return None
        sql = u"SELECT * FROM {0} WHERE CODE = {1} AND ACCOUNT LIKE '%{2}%'".format(tablename, code, account)
        # print(sql)
        db = self.connect()
        cursor = db.cursor()
        results = []
        try:
            cursor.execute(sql)
            db.commit()
            results = cursor.fetchall()
        except Exception as e:
            # 表存在就回滚操作
            db.rollback()
            print(e)
        finally:
            cursor.close()
            db.close()
        if len(results) > 0:
            return [list(x) for x in results]
        else:
            return None

    def selectAllRecordsOfAccount(self, tablename = 'klq', account = '华泰'):
        if tablename != 'klq':
            tablename = 'parents'
        if account == None or len(account) <= 0:
            print('[ERROR] 账户错误：{0}'.format(account))
            return None
        sql = u"SELECT * FROM {0} WHERE ACCOUNT LIKE '%{1}%'".format(tablename, account)
        # print(sql)
        db = self.connect()
        cursor = db.cursor()
        results = []
        try:
            cursor.execute(sql)
            db.commit()
            results = cursor.fetchall()
        except Exception as e:
            # 表存在就回滚操作
            db.rollback()
            print(e)
        finally:
            cursor.close()
            db.close()
        if len(results) > 0:
            return [list(x) for x in results]
        else:
            return None

    ################################################
    # INSERT
    ################################################

    # 插入数据
    def insertDataToTable(self, tablename, keys, values):
        sql_keys = keys
        if len(tablename) == 0:
            tablename = 'klq'
        if len(sql_keys) == 0:
            sql_keys = self.sql_keys
        sql_values = values
        d = dict(zip(sql_keys, sql_values))
        # 字段超多时（本例中 22 个字段，用下面方法配合字典插入）
        sql = '''INSERT INTO %s(%s) values (%s)'''
        key_list = []
        value_list= []
        for k, v in d.items():
            key_list.append(k)
            value_list.append('%%(%s)s' % k)
        sql = sql % (tablename, ','.join(key_list),','.join(value_list))
        print(sql, d)
        db = self.connect()
        cursor = db.cursor()
        try:
            cursor.execute(sql, d)
            db.commit()
        except Exception as e:
            db.rollback()
            print(e)
        finally:
            cursor.close()
            db.close()

if __name__ == "__main__":
    db = dealRecordDBHelper()
    pass