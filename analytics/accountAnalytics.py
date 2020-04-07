# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime

import pandas as pd

from database.dealRecordDBHelper import dealRecordDBHelper
from spider.common.dealRecordModel import *
from analytics.holdingModel import holdingModel

class accountAnalytics:

    def __init__(self, strategy = 'klq'):
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.db = dealRecordDBHelper()
        self.strategy = strategy
        if strategy == 'klq':
            self.owner = '康力泉'
        elif strategy == 'lsy':
            self.owner = '李淑云'
        elif strategy == 'ksh':
            self.owner = '康世海'
    
    def getFundCode(self, code, showFolder = False):
        if code == None or len(code) == 0:
            return None
        db_results = self.db.selectAllRecordsOfCode(code)
        # 账户下的所有记录
        records = []
        for x in db_results:
            model = dealRecordModelFromValues(x)
            records.append(model.__dict__)
        # 通过 DataFrame 分析
        df = pd.DataFrame(records, columns=dealRecordModelKeys())
        folder = os.path.join(self.folder, 'output', 'fundCode', code)
        return self.analytics(df, folder, False)

    def getAccount(self, account, showFolder = False):
        tablename = ''
        if self.strategy == 'klq':
            tablename = 'klq'
        else:
            tablename = 'parents'
        if account == None or len(account) == 0:
            return None
        db_results = self.db.selectAllRecordsOfAccount(tablename, account)
        # 账户下的所有记录
        records = []
        for x in db_results:
            model = dealRecordModelFromValues(x)
            records.append(model.__dict__)
        # 通过 DataFrame 分析
        df = pd.DataFrame(records, columns=dealRecordModelKeys())
        folder = os.path.join(self.folder, 'output', 'account', tablename, account)
        return self.analytics(df, folder, True)

    def analytics(self, df, folder, showFolder = False):
        # print(df)
        codes = df.code.unique()
        results = []
        if not os.path.exists(folder):
            os.makedirs(folder)
        for i in range(0, len(codes)):
            code = codes[i]
            sub_df = df[df['code'] == code]
            sub_df = sub_df.reset_index(drop=True)
            name = sub_df.name.values[0]
            sub_df.to_csv(os.path.join(folder, '{0}_{1}.csv'.format(code, name.replace('/','_'))))
            # 逐一分析每一个品种
            results.append(self.analyticsStatusOfCode(code, sub_df.values))
        # [print(x) for x in results]
        # result_df = pd.DataFrame(results, columns=['date', 'code', 'name', 'status', 'holding_nav', 'holding_volume', 'holding_money', 'total_fee', 'holding_gain', 'history_gain', 'total_cash_dividend', 'category1', 'category2', 'category3', 'categoryId'])
        result_df = pd.DataFrame(results, columns=familyHoldingDBKeys())
        # result_df['持仓净值'] = result_df['持仓净值'].astype(float)
        result_df = result_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
        result_df = result_df.reset_index(drop=True)
        result_df.to_csv(os.path.join(folder, 'holding_status.csv'), sep=',', encoding = "utf-8")
        if showFolder and sys.platform.startswith('win'):
            os.startfile(folder)
        return result_df

    # 分析对应品种的
    def analyticsStatusOfCode(self, code, df):
        # 成交记录数量大于 0 
        if len(df) > 0:
            # if code == '501018':
            #     print()
            # 初始化（第一笔一定是买，否则怎么卖呢？）
            holdingItem = holdingModel()
            initItem = list(df).pop(0)
            record = dealRecordModelFromValues(initItem)
            holdingItem.initWithDealRecord(record)
            date = holdingItem.date
            # 处理之后所有的交易
            for i in range(1, len(df)):
                x = list(df[i])
                record = dealRecordModelFromValues(x)
                # 如果现在已经是卖空态，说明这是一次全新交易的开始，重新初始化
                if holdingItem.isEmpty:
                    if '买' not in record.dealType:
                        print('[出错了]   {0} {1} 初始化时，依然不是买入，逻辑错误'.format(code, date))
                        # exit(1)
                        continue
                    holdingItem.initWithDealRecord(record)
                    continue
                holdingItem.calcWithDealRecord(record)
            # 修正历史盈亏
            holdingItem.finish()
            return holdingItem.__dict__
        else:
            return None

if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'lsy\'：李淑云 \'ksh\'：康世海')
        exit()
    # 传入配置，开始流程
    analytics = accountAnalytics(strategy = strategy)
    # analytics.get()


