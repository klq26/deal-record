# -*- coding: utf-8 -*-
import os
import sys
import json
import pymysql

import pandas as pd
import numpy as np

from login.account import account
from spider.common.dealRecordModel import *

class holdingDBHelper:
    
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
    # SELECT
    ################################################

    # 返回家庭持仓详细情况，合并不同用户的相同基金操作，比如多人、多组合都买了 100032，则合并为一条记录
    def selectAllCombineFundHoldings(self):
        sql = u"SELECT * FROM fund_holding"
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
            holdings = []
            for x in results:
                values = np.array(x).tolist()
                holdings.append(familyHoldingModelFromValues(values))
            return holdings
        else:
            return None

    # 返回家庭持仓详细情况，不合并不同用户的相同基金操作，比如多人、多组合都买了 100032，则保留多条 100032 记录
    def selectAllIsolatedFundHoldings(self):
        sql = u"SELECT * FROM family_holding"
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
            holdings = []
            for x in results:
                values = np.array(x).tolist()
                holdings.append(familyHoldingModelFromValues(values))
            return holdings
        else:
            return None