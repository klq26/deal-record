# -*- coding: utf-8 -*-
import os
import sys
import json
import pymysql

from login.account import account

class fundDBHelper:
    
    def __init__(self):
        # 取用户名密码
        self.account = account()
        # 打开数据库
        self.ip_address = ''
        if sys.platform.startswith('win'):
            self.ip_address = '112.125.25.230'
        elif sys.platform.startswith('linux'):
            self.ip_address = '127.0.0.1'

    def connect(self):
        return pymysql.connect(self.ip_address, self.account.user, self.account.password, 'fund')

    # 获取数据库中所有的库存表
    def getAllCodesInDB(self):
        # sql = "SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema='fund' AND table_type='base table';"
        sql = "SHOW TABLES WHERE Tables_in_fund LIKE 'nav_%'"
        db = self.connect()
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
            results = cursor.fetchall()
            if len(results) > 0:
                return [x[0].replace('nav_','') for x in list(results)]
        except Exception as e:
            # 表存在就回滚操作
            db.rollback()
            print(e)
        finally:
            cursor.close()
            db.close()

    # 创建基金基础信息表
    def addFundInfoTableIfNeeded(self):
        sql = """
        CREATE TABLE fund_info (
        fundCode VARCHAR(6) NOT NULL COLLATE 'utf8_unicode_ci',
        fundName VARCHAR(20) NULL COLLATE 'utf8_unicode_ci',
        foundDate VARCHAR(10) NULL COLLATE 'utf8_unicode_ci',
        fundType VARCHAR(10) NULL COLLATE 'utf8_unicode_ci',
        feeRate FLOAT(12) NULL,
        feeRateDiscount FLOAT(12) NULL,
        sell VARCHAR(100) NULL COLLATE 'utf8_unicode_ci',
        holding VARCHAR(100) NULL COLLATE 'utf8_unicode_ci',
        buyConfirmDay INT(11) NULL,
        buyQueryDay INT(11) NULL,
        canCheckGainDay INT(11) NULL,
        sellConfirmDay INT(11) NULL,
        sellQueryDay INT(11) NULL,
        moneyBackDay INT(11) NULL,
        PRIMARY KEY (fundCode)
        )
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

    # 动态添加表：根据表名创建
    def addNavTableIfNeeded(self, tablename):
        if tablename in self.getAllCodesInDB():
            print('Table: nav_{0} exist.'.format(tablename))
        sql = 'CREATE TABLE nav_{0} (date VARCHAR(20) NOT NULL, nav_unit FLOAT NOT NULL, nav_acc FLOAT NOT NULL, PRIMARY KEY (date))'.format(tablename)
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
    
    # 返回最新一条数据的日期
    def selectLatestRecordFromTable(self, code):
        sql = u'SELECT * FROM nav_{0} ORDER BY DATE DESC LIMIT 1;'.format(code)
        print(sql)
        db = self.connect()
        cursor = db.cursor()
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
            # 返回第一条数据的日期('data', 'nav_unit', 'nav_acc')
            return results[0][0]
        else:
            return None

    # 插入数据
    def insertDataToTable(self, tablename, keys, values):
        sql_keys = keys # ['date', 'nav_unit', 'nav_acc']
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

    # 通过 fundInfoSpider 生成的 json 数据直接插入对应的数据库
    def insertFundByJonsData(self, jsonData):
        # self.addFundInfoTableIfNeeded()
        # 插入详细信息
        detailInfo = jsonData['detailInfo']
        code = detailInfo['fundCode']
        info_keys = ['fundCode', 'fundName', 'foundDate', 'fundType', 'feeRate', 'feeRateDiscount', 'sell', 'holding', 'buyConfirmDay', 'buyQueryDay', 'canCheckGainDay', 'sellConfirmDay', 'sellQueryDay', 'moneyBackDay']
        # 组织数组
        sell_array = []
        for item in detailInfo['sell']:
            sell_array.append(item['name'] + ',' + item['value'])
        holding_array = []
        for item in detailInfo['holding']:
            holding_array.append(item['name'] + ',' + item['value'])
        # 组织 value
        info_values = [detailInfo['fundCode'], detailInfo['fundName'], detailInfo['foundDate'], detailInfo['fundType'], detailInfo['buy']['feeRate'], detailInfo['buy']['feeRateDiscount'], '-'.join(sell_array), '-'.join(holding_array), detailInfo['confirm']['buyConfirmDay'], detailInfo['confirm']['buyQueryDay'], detailInfo['confirm']['canCheckGainDay'], detailInfo['confirm']['sellConfirmDay'], detailInfo['confirm']['sellQueryDay'], detailInfo['confirm']['moneyBackDay']]
        self.insertDataToTable('fund_info', keys = info_keys, values = info_values)

        # 插入净值数据
        datalist = jsonData['navInfo']
        self.addNavTableIfNeeded(code)
        for item in datalist:
            items = []
            items.append(item['date'])
            items.append(item['navUnit'])
            items.append(item['navAcc'])
            self.insertDataToTable('nav_{0}'.format(code), keys = ['date', 'nav_unit', 'nav_acc'], values = items)

if __name__ == "__main__":
    db = fundDBHelper()
    db.addNavTableIfNeeded('100032')
    pass