# -*- coding: utf-8 -*-
import os
import sys
import json
import pymysql

import pandas as pd
import numpy as np

from login.account import account
from spider.common.dealRecordModel import *

class dealRecordDBHelper:
    
    def __init__(self):
        # 取用户名密码
        self.account = account()
        # 打开数据库
        self.ip_address = ''
        self.sql_keys = dealRecordModelKeys()
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

    # 创建家庭持仓表
    def createFamilyHoldingTableIfNeeded(self):
        sql = """
        CREATE TABLE `family_holding` (
            `id` INT(11) NULL DEFAULT NULL,
            `date` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `code` VARCHAR(6) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `name` VARCHAR(30) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `status` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `holding_nav` DECIMAL(10,4) NULL DEFAULT NULL,
            `holding_volume` DECIMAL(10,2) NULL DEFAULT NULL,
            `holding_money` DECIMAL(10,2) NULL DEFAULT NULL,
            `holding_gain` DECIMAL(10,2) NULL DEFAULT NULL,
            `history_gain` DECIMAL(10,2) NULL DEFAULT NULL,
            `total_cash_dividend` DECIMAL(10,2) NULL DEFAULT NULL,
            `total_fee` DECIMAL(10,2) NULL DEFAULT NULL,
            `account` VARCHAR(20) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category1` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category2` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `category3` VARCHAR(10) NULL DEFAULT NULL COLLATE 'utf8_unicode_ci',
            `categoryId` INT(11) NULL DEFAULT NULL,
            UNIQUE INDEX `id` (`id`)
        )
        COMMENT='全家当前持仓情况'
        COLLATE='utf8_unicode_ci'
        ENGINE=InnoDB
        ROW_FORMAT=COMPACT
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

    # 返回特定基金代码的所有成交记录（从康力泉和父母两张表中联合查询）
    def selectAllRecordsOfCode(self, code = ''):
        if len(code) <= 0:
            print('[ERROR] 代码错误：{0}'.format(code))
            return None
        sql = u"(SELECT * FROM klq WHERE CODE = {0}) UNION  (SELECT * FROM parents WHERE CODE = {1}) ORDER BY DATE ASC;".format(code, code)
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

    # 返回特定账户的所有成交记录
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

    ################################################
    # DataFrame adapter
    ################################################

    def insertFamilyHoldingByDataFrame(self, df):
        for item in df.values:
            values = np.array(item).tolist()
            # print(values, type(values))
            self.insertDataToTable('family_holding',familyHoldingDBKeys(), values)
        pass

    def insertFamilySelloutByDataFrame(self, df):
        for item in df.values:
            values = np.array(item).tolist()
            # print(values, type(values))
            self.insertDataToTable('family_sellout',familyHoldingDBKeys(), values)
        pass

    def insertFundHoldingByDataFrame(self, df):
        for item in df.values:
            values = np.array(item).tolist()
            # print(values, type(values))
            self.insertDataToTable('fund_holding',familyHoldingDBKeys(), values)
        pass

    ################################################
    # TRUNCATE
    ################################################

    def truncateTable(self, tablename):
        sql = u"truncate {0}".format(tablename)
        # print(sql)
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

if __name__ == "__main__":
    db = dealRecordDBHelper()
    pass