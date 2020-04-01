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
    
    ################################################
    # COMMON
    ################################################
    # 连接数据库
    def connect(self):
        return pymysql.connect(self.ip_address, self.account.user, self.account.password, 'fund')

    ################################################
    # CREATE
    ################################################

    # 创建基金基础信息表
    def createFundInfoTableIfNeeded(self):
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

    # 动态添加基金历史净值表：根据代码创建
    def createFundNavTableIfNeeded(self, tablename):
        if tablename in self.selectAllFundNavCodes():
            print('Table: nav_{0} exist.'.format(tablename))
            return
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

    ################################################
    # SELECT
    ################################################

    # 获取数据库中所有的库存表
    def selectAllFundNavCodes(self):
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

    # 返回最新一条基金净值数据
    def selectLatestRecordFromFundNavTable(self, code):
        sql = u'SELECT * FROM nav_{0} ORDER BY DATE DESC LIMIT 1;'.format(code)
        # print(sql)
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
            return results[0]
        else:
            return None

    # 返回特定日期的基金净值数据
    def selectFundNavByDate(self, code, date):
        if code not in self.selectAllFundNavCodes():
            return [date, -1, -1]
        sql = u"SELECT * FROM nav_{0} WHERE DATE = '{1}';".format(code, date)
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
            # 返回第一条数据的日期('data', 'nav_unit', 'nav_acc')
            return results[0]
        else:
            return None

    # 返回特定日期前一个有效净值日的基金净值数据
    def selectFundNavBeforeDate(self, code, date):
        if code not in self.selectAllFundNavCodes():
            return [date, -1, -1]
        sql = u"SELECT * FROM nav_{0} WHERE DATE < '{1}' ORDER BY DATE DESC LIMIT 1;".format(code, date)
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
            # 返回第一条数据的日期('data', 'nav_unit', 'nav_acc')
            return results[0]
        else:
            return None

    ################################################
    # INSERT
    ################################################

    # 插入数据
    def insertDataToTable(self, tablename, keys, values):
        sql_keys = keys
        if len(sql_keys) == 0:
            sql_keys = ['date', 'nav_unit', 'nav_acc']
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
    # JSON adapter
    ################################################

    # 通过 fundInfoSpider 生成的 json 数据直接插入对应的数据库
    def insertFundByJonsData(self, jsonData):
        # self.createFundInfoTableIfNeeded()
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
        self.createFundNavTableIfNeeded(code)
        for item in datalist:
            items = []
            items.append(item['date'])
            items.append(item['navUnit'])
            items.append(item['navAcc'])
            self.insertDataToTable('nav_{0}'.format(code), keys = ['date', 'nav_unit', 'nav_acc'], values = items)

    # 通过 dividenInfoSpider 生成的 json 数据直接插入对应的数据库
    def insertFundDividendByJonsData(self, jsonData):
        # {
        #     "代码": "000071",
        #     "名称": "华夏恒生ETF联接A",
        #     "分红": [
        #         {
        #             "年份": "2020年",
        #             "权益登记日": "2020-01-16",
        #             "除息日": "2020-01-15",
        #             "每份分红": "每份派现金0.0270元",
        #             "分红发放日": "2020-01-21"
        #         }],
        #     "拆分": [
        #         {
        #             "年份": "2019年",
        #             "拆分折算日": "2019-12-16",
        #             "拆分类型": "份额折算",
        #             "拆分折算比例": "1:1.0107"
        #         }]
        # }
        sqlDict = {'代码': jsonData['代码'], '名称': jsonData['名称']}
        dividends = jsonData['分红']
        splites = jsonData['拆分']
        if len(dividends) > 0:
            # 有分红信息
            for dividend in dividends:
                sqlDict.update(dividend)
                db_keys = list(sqlDict.keys())
                db_values = list(sqlDict.values())
                self.insertDataToTable('fund_dividend', db_keys, db_values)
        if len(splites) > 0:
            # 有分红信息
            for split in splites:
                sqlDict.update(split)
                db_keys = list(sqlDict.keys())
                db_values = list(sqlDict.values())
                self.insertDataToTable('fund_split', db_keys, db_values)

if __name__ == "__main__":
    db = fundDBHelper()
    db.createFundNavTableIfNeeded('100032')
    pass