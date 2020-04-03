# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime

import pandas as pd

from database.dealRecordDBHelper import dealRecordDBHelper
from spider.common.dealRecordModel import *

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
    
    def getAccount(self, account):
        tablename = ''
        if self.strategy == 'klq':
            tablename = 'klq'
        else:
            tablename = 'parents'
        if account == None or len(account) == 0:
            return None
        db_results = self.db.selectAllRecordsOfAccount(tablename, account)
        # 是否场内
        isInner = False
        if '华宝' in account or '华泰' in account:
            isInner = True
        # 账户下的所有记录
        records = []
        for x in db_results:
            model = dealRecordModelFromValues(x)
            records.append(model.__dict__)
        # 通过 DataFrame 分析
        df = pd.DataFrame(records, columns=dealRecordModelKeys())
        # print(df)
        codes = df.code.unique()
        names = df.name.unique()
        results = []
        folder = os.path.join(self.folder, 'output', tablename, account)
        if not os.path.exists(folder):
            os.makedirs(folder)
        for i in range(0, len(codes)):
            code = codes[i]
            name = names[i]
            sub_df = df[df['code'] == code]
            sub_df.to_csv(os.path.join(folder, '{0}_{1}.csv'.format(code, name)))
            # 逐一分析每一个品种
            results.append(self.getCode(code, sub_df.values, isInner).split('\t'))
        # [print(x) for x in results]
        result_df = pd.DataFrame(results, columns=['最后日期','代码', '名称', '持仓净值','持仓份额','持仓金额','历史收益'])
        result_df['持仓净值'] = result_df['持仓净值'].astype(float)
        result_df['持仓份额'] = result_df['持仓份额'].astype(float)
        result_df['持仓金额'] = result_df['持仓金额'].astype(float)
        result_df['历史收益'] = result_df['历史收益'].astype(float)
        result_df = result_df.sort_values('持仓份额',ascending=False)
        result_df.to_excel(os.path.join(folder, '{0}_{1}.xlsx'.format(tablename, account)))
        if sys.platform.startswith('win'):
            os.startfile(folder)


    # 分析对应品种的
    def getCode(self, code, df, isInner):
        holding_nav = 0
        holding_volume = 0
        holding_money = 0
        history_gain = 0
        
        name = ''

        dateIdx = 1
        codeIdx = 2
        namdIdx = 3
        opIdx = 4
        navIdx = 5
        volumeIdx = 7
        # TODO 这里按 8 还是 10 计算，略有出入。按 10 算，就是把付出的手续费也加进去了，我觉得按 10 合理。因为手续费也不能无视
        moneyIdx = 10
        if isInner:
            moneyIdx = 8

        info = u"日期：{0} 代码：{1} 持仓净值：{2} 持仓份额：{3} 持仓金额：{4}"

        # db = dealRecordDBHelper()
        # results = db.selectAllRecordsOfCode(tablename = 'klq', code = '159915', account = '华泰')

        if len(df) > 0:
            # if code == '501018':
            #     print()
            # 初始化（第一笔一定是买，否则怎么卖呢？）
            initItem = list(df).pop(0)
            date = initItem[dateIdx]
            name = initItem[namdIdx]
            holding_nav = round(initItem[navIdx], 4)
            holding_volume = initItem[volumeIdx]
            holding_money = round(initItem[moneyIdx], 2)
            if not isInner:
                # 场外基金的摊薄成本必须得加上手续费一起算，money/volume 成本会上升
                holding_nav = round(holding_money / holding_volume, 4)
            print('\n\n\n[初始化]   {0}'.format(info.format(date, code, holding_nav, holding_volume, holding_money)))
            # 处理之后所有的交易
            for i in range(1, len(df)):
                x = df[i]
                date = x[dateIdx]
                code = x[codeIdx]
                op = x[opIdx]
                nav = x[navIdx]
                volume = x[volumeIdx]
                money = x[moneyIdx]
                # 如果现在已经是卖空态，说明这是一次全新交易的开始
                if holding_volume == 0:
                    if '买' not in op:
                        print('[出错了]   {0} {1} 初始化时，依然不是买入，逻辑错误'.format(code, date))
                        # exit(1)
                        continue
                    holding_nav = round(nav, 4)
                    holding_volume = volume
                    holding_money = round(money, 2)
                    print('[初始化]   {0}'.format(info.format(date, code, holding_nav, holding_volume, holding_money)))
                    continue
                if '卖' in op:
                    volume = -volume
                    money = -money
                    # 操作系卖出
                    gain = round((nav - holding_nav) * -volume, 2)
                    history_gain = round(history_gain + gain, 2)
                    status = '卖出后'
                    if holding_volume == -volume:
                        # 卖空，更新累计收益
                        holding_nav = round(0, 4)
                        holding_money = round(0, 2)
                        holding_volume = 0
                        status = '清仓后'
                    else:
                        holding_nav = round((holding_money + money) / (holding_volume + volume), 4)
                        holding_money = round(holding_money + money, 2)
                        holding_volume = holding_volume + volume
                    print('[{0}]   {1} 本次收益：{2} 累计收益：{3}'.format(status, info.format(date, code, holding_nav, holding_volume, holding_money), gain, history_gain))
                else:
                    status = '买入后'
                    if '分红' in op:
                        if money == 0:
                            # 红利再投资
                            status = '分份额'
                            # print('[分份额]   {1} 本次收益：{2} 累计收益：{3}'.format(info.format(date, holding_nav, holding_volume, holding_money)))
                        elif volume == 0:
                            # 现金分红
                            gain = round(money, 2)
                            history_gain = round(history_gain + gain, 2)
                            print('[分现金]   {0} 本次收益：{1} 累计收益：{2}'.format(info.format(date, code, holding_nav, holding_volume, holding_money), gain, history_gain))
                            continue
                        else:
                            print('[出错了]   {0} {1} 分红数据有误'.format(code, date))
                            exit(1)
                    holding_nav = round((holding_money + money) / (holding_volume + volume), 4)
                    holding_money = round(holding_money + money, 2)
                    holding_volume = holding_volume + volume
                    print('[{0}]   {1}'.format(status, info.format(date, code, holding_nav, holding_volume, holding_money)))
                
            result = '\n[结束时]   日期：{0} 代码：{1} 历史收益：{2} 持仓净值：{3} 持仓份额：{4} 持仓金额：{5}'.format(date, code, round(history_gain, 2), round(holding_nav, 4), round(holding_volume, 4), round(holding_money, 4))
            print(result)
            return '\t'.join([date, code, name, str(round(holding_nav, 4)), str(round(holding_volume, 4)), str(round(holding_money, 4)), str(round(history_gain, 2))])
        else:
            return '{0} 未知'.format(code)

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


