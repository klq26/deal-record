# -*- coding: utf-8 -*-

import os
import sys

import pandas as pd

from analytics.holdingModel import holdingModel
from analytics.accountAnalytics import accountAnalytics

class analyticsManager:
    """
    就一个 helper 类，防止外部手动书写 account 名称造成的各种小失误
    """

    def __init__(self, strategy = 'klq'):
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.strategy = strategy
    
    def klqDBAccountNames(self):
        klq_db_accounts = ['华泰证券', '华宝证券', '康力泉_天天', '康力泉_且慢_150份', '康力泉_且慢_S定投', '康力泉_蛋卷_螺丝钉指数基金组合', '康力泉_蛋卷_钉钉宝90天组合', '康力泉_蛋卷_钉钉宝365天组合', '支付宝']
        return klq_db_accounts
    
    def klqFinanceAccountNames(self):
        klq_finance_accounts = ['华泰证券', '华宝证券', '天天基金', '且慢 150 份', '且慢 S 定投', '螺丝钉', '钉钉宝90', '钉钉宝365', '支付宝']
        return klq_finance_accounts
    
    def parentsDBAccountNames(self):
        parents_db_accounts = ['李淑云_天天', '李淑云_蛋卷_螺丝钉指数基金组合', '李淑云_蛋卷_钉钉宝90天组合', '李淑云_蛋卷_钉钉宝365天组合', '康世海_且慢_稳稳的幸福', '康世海_蛋卷_螺丝钉指数基金组合', '康世海_蛋卷_钉钉宝90天组合', '康世海_蛋卷_钉钉宝365天组合']
        return parents_db_accounts

    def parentsFinanceAccountNames(self):
        parents_finance_accounts = ['天天基金母', '螺丝钉母', '钉钉宝90母', '钉钉宝365母', '稳稳的幸福父', '螺丝钉父', '钉钉宝90父', '钉钉宝365父']
        return parents_finance_accounts

    def getFamilyHoldingUniqueCodes(self):
        folder = os.path.join(self.folder, 'output', 'account', 'family')
        if not os.path.exists(folder):
            os.makedirs(folder)
        holding_path = os.path.join(folder, 'all_holding_status.csv')
        if not os.path.exists(holding_path):
            # 没有文件就先调用整理，这种场景应该不常见
            self.getFamilyHoldingSelloutStatus()
        holding_df = pd.read_csv(holding_path)
        uniqueCodes_df = holding_df.drop_duplicates(['code'])
        uniqueCodes_df = uniqueCodes_df.sort_values(['code'])
        uniqueCodes_df['code'] = [str(x).zfill(6) for x in uniqueCodes_df.code.values]
        keys = uniqueCodes_df['code']
        values = uniqueCodes_df['name']
        # print(len(keys))
        return dict(zip(keys, values))

    # 获取整个家庭当前持仓的资产配置情况，已清仓的历史情况。
    def getFamilyHoldingSelloutStatus(self):
        """
        获取整个家庭当前持仓的资产配置情况及已清仓的历史情况。
        当前持仓：all_holding_status.csv
        历史清仓：all_sellout_status.csv
        """
        holding_df = pd.DataFrame()
        sellout_df = pd.DataFrame()
        # 康力泉
        klq_db_accounts = self.klqDBAccountNames()
        klq_finance_accounts = self.klqFinanceAccountNames()
        aa = accountAnalytics('klq')
        for i in range(0,len(klq_db_accounts)):
            db_account = klq_db_accounts[i]
            finance_account = klq_finance_accounts[i]
            result_df = aa.getAccount(db_account)
            result_df['account'] = finance_account
            
            sub_holding_df = result_df[result_df['holding_volume'] > 0]
            sub_sellout_df = result_df[result_df['holding_volume'] == 0]

            sub_holding_df = sub_holding_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
            sub_holding_df = sub_holding_df.reset_index(drop=True)
            holding_df = holding_df.append(sub_holding_df)

            sub_sellout_df = sub_sellout_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
            sub_sellout_df = sub_sellout_df.reset_index(drop=True)
            sellout_df = sellout_df.append(sub_sellout_df)
        # 父母
        parents_db_accounts = self.parentsDBAccountNames()
        parents_finance_accounts = self.parentsFinanceAccountNames()
        aa = accountAnalytics('parents')
        for i in range(0,len(parents_db_accounts)):
            db_account = parents_db_accounts[i]
            finance_account = parents_finance_accounts[i]
            result_df = aa.getAccount(db_account)
            result_df['account'] = finance_account
            
            sub_holding_df = result_df[result_df['holding_volume'] > 0]
            sub_sellout_df = result_df[result_df['holding_volume'] == 0]

            sub_holding_df = sub_holding_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
            sub_holding_df = sub_holding_df.reset_index(drop=True)
            holding_df = holding_df.append(sub_holding_df)

            sub_sellout_df = sub_sellout_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
            sub_sellout_df = sub_sellout_df.reset_index(drop=True)
            sellout_df = sellout_df.append(sub_sellout_df)

        # sort
        holding_df = holding_df.sort_values(['account', 'categoryId'],ascending=[True, True])
        holding_df = holding_df.reset_index(drop=True)

        sellout_df = sellout_df.sort_values(['account', 'categoryId'],ascending=[True, True])
        sellout_df = sellout_df.reset_index(drop=True)

        # output
        folder = os.path.join(self.folder, 'output', 'account', 'family')
        if not os.path.exists(folder):
            os.makedirs(folder)
        holding_df.to_csv(os.path.join(folder, 'all_holding_status.csv'))
        sellout_df.to_csv(os.path.join(folder, 'all_sellout_status.csv'))
        return (holding_df, sellout_df)

    def getFundHoldingStatus(self):
        holding_df = pd.DataFrame()
        aa = accountAnalytics()
        for code in self.getFamilyHoldingUniqueCodes().keys():
            sub_holding_df = aa.getFundCode(code)
            holding_df = holding_df.append(sub_holding_df)
        holding_df = holding_df.sort_values(['categoryId', 'holding_money'],ascending=[True, False])
        holding_df = holding_df.reset_index(drop=True)
        # output
        folder = os.path.join(self.folder, 'output', 'fundCode')
        holding_df.to_csv(os.path.join(folder, 'all_code_holding_status.csv'))
        return holding_df


if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'lsy\'：李淑云 \'ksh\'：康世海')
        exit()
    # 传入配置，开始流程
    analytics = analyticsManager(strategy = strategy)
    # analytics.get()


