# -*- coding: utf-8 -*-
import os
import sys
import json

import pandas as pd
import numpy as np

# NOTE：取值是 “资金流水”
# 这个类是为了对接之前手工修改过格式的成交记录的，仅作对接，无需扩展。
# ★huataiSpider 会调用这个类并继承该类的数据，无需手动调用当前类

global_name = '华泰证券'

# 0. 定义预期数据。所有 suppose 开头的变量都是需要验证的内容。当与预期不符时，程序应该报错并终止 #

# 预期文件的全部列名（第一次是从 xlsx 中复制过来的）
suppose_all_file_columns = ['流水号', '发生日期', '证券名称', '证券代码', '买卖标志', '业务名称', '成交价格', '成交数量', '发生金额', '剩余金额', '佣金', '股东代码', '备注']
# 我们实际需要的列名
suppose_needed_columns=['流水号', '发生日期', '业务名称', '证券代码', '证券名称', '买卖标志', '成交价格', '成交数量', '发生金额', '佣金', '备注']
# 证券代码取值范围
suppose_codes = {'name': '证券代码', 'value': ['518880', '510500', '000836', '600879', '000017', '600857', '600861', '000428', '511880', '510050', '159920', '162411', '510300', '510900', '601939', '511880', '511010', '501018', '162411', '940037', '940018', '159920', '510900', '204007', '204007', '131810', 'nan', '204001', '131800', '159938', '004749', '511980', '512980', '511990', '512100', '512580', '512880', '519888', '159915', '510050', '510300', '003474', '159902', '159902', ' ']}
# 证券名称取值范围
suppose_names = {'name': '证券名称', 'value': ['黄金ETF', '500ETF', '鑫茂科技', '航天电子', '深中华A', '宁波中百', '北京城乡', '华天酒店', '银华日利', '50ETF', '恒生ETF', '华宝油气', '300ETF', 'H股ETF', '建设银行', '国债ETF', '南方原油', '紫金货币', '天天发1', 'GC007', 'Ｒ-001', ' ', 'GC001', 'Ｒ-003', '广发医药', '现金添富', '传媒ETF', '华宝添益', '1000ETF', '环保ETF', '证券ETF', '添富快线', '创业板', '中 小 板']}
# 委托类别取值范围
suppose_operates = {'name': '买卖标志', 'value': ['买入', '卖出', '其他']}
# 业务名称取值范围
suppose_bussiness_name = {'name': '业务名称', 'value': ['买入', '卖出', '其他', '基金资金拨出', '基金资金拨入', '证券买入', '拆出质押购回', '股息入帐', '证券卖出', '质押回购拆出', '银行转存', '资管转让资金上账', '银行转取', '利息归本', 'ETF现金替代退款', '红股入帐', '货币基金申购', '货币基金赎回', '开放基金赎回', '开放基金赎回返款']}
# 需要校验的列集合
suppose_justify_columns = [suppose_codes, suppose_names, suppose_operates, suppose_bussiness_name]

class huataiHistory:

    def __init__(self):
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        # TEST 显示列名，列唯一值
        # df = pd.read_excel(os.path.join(self.folder, 'input', global_name + u'2015-2019.xlsx'))
        # file_columns = df.columns
        # # 列名
        # print(list(file_columns))
        # # 列唯一值
        # for cate in df.columns:
        #     print("{" + "'name': '{0}', 'value': [{1}]".format(cate, ', '.join(["'{0}'".format(x) for x in df[cate].unique()])) + "}")
        # exit(1)

        # 1. 读取文件并校验目标文件的列名是否符合预期 #
        df = pd.read_excel(os.path.join(self.folder, 'input', global_name + u'2015-2019.xlsx'))
        # 验证数据
        df = self.verifyDataFrame(df)
        # 调整列
        self.needed_df = self.modifyDataFrame(df)
    
    def verifyDataFrame(self, needed_df):
        file_columns = needed_df.columns
        is_columns_equals = file_columns == suppose_all_file_columns
        for x in range(0,len(is_columns_equals)):
            if is_columns_equals[x] == False:
                print(global_name + '原始数据列名有误：{0} 预期：{1} vs 实际：{2}'.format(x, suppose_all_file_columns[x], file_columns[x]))
                exit(1)
                break
        print('列名 校验通过')
        # 2. 取目标列 #
        needed_df = pd.DataFrame(needed_df, columns=suppose_needed_columns)
        # 3. 校验特殊列的合法性 #
        for columnDict in suppose_justify_columns:
            target_column_values = needed_df[columnDict['name']].unique()
            for value in target_column_values:
                if str(value) not in columnDict['value']:
                    print(global_name + '原始数据列值有误，目标值：{0} 不在列：{1} 的预期值之中。'.format(value, columnDict['name']))
                    exit(1)
            print('{0} 校验通过'.format(columnDict['name']))
        return needed_df

    def modifyDataFrame(self, needed_df):
        # 4. 调整（增删改查） dataframe 数据列 #
        needed_df['nav_acc'] = needed_df['成交价格']
        needed_df['fee'] = needed_df['佣金']
        needed_df.drop(columns=['佣金'])
        needed_df['occurMoney'] = needed_df['发生金额']
        needed_df['account'] = global_name
        # 5. 生成 json 对象
        # 按 model key 值顺序重组 dataframe
        reindex_columns=['流水号', '发生日期', '证券代码', '证券名称', '买卖标志', '成交价格', 'nav_acc', '成交数量', '发生金额', 'fee', 'occurMoney', 'account', '备注']
        needed_df = needed_df.reindex(columns=reindex_columns)
        # print(needed_df)
        return needed_df

    def get(self):
        # 模型字段数组
        all_model_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'note']
        records = []
        money_funds = []
        others = []
        for x in self.needed_df.values:
            item = dict(zip(all_model_keys, list(x)))
            # 最后一次修改
            # 日期格式统一
            item['date'] = '{0}'.format(str(item['date'])[0:10].replace('-','/'))
            item['code'] = str(item['code'])
            # 不要负值
            if float(item['volume']) < 0:
                item['volume'] = round(float(item['volume']) * -1, 2)
            if float(item['dealMoney']) < 0:
                item['dealMoney'] = round(float(item['dealMoney']) * -1, 2)
            if float(item['occurMoney']) < 0:
                item['occurMoney'] = round(float(item['occurMoney']) * -1, 2)
            # if item['dealType'] == '基金申购':
            #     item['dealType'] = '买入'
            if item['dealType'] == '买入':
                item['occurMoney'] = item['dealMoney'] + item['fee']
            elif item['dealType'] == '卖出':
                # 华泰证券里面，发生金额是到手金额，所以总流水应该是 deal + fee
                item['occurMoney'] = item['dealMoney'] - item['fee']
            if '股息入账' in item['note']:
                item['dealType'] = '分红'
            item['volume'] = abs(item['volume'])
            item['occurMoney'] = round(float(item['occurMoney']), 2)
            item['dealMoney'] = round(item['dealMoney'], 2)
            # 非交易性操作
            if item['code'] == ' ' or item['name'] == ' ':
                others.append(item)
            elif item['name'] in ['银华日利', '紫金货币', '天天发1', 'GC007', 'Ｒ-001', 'GC001', 'Ｒ-003', '现金添富', '华宝添益', '添富快线']:
                money_funds.append(item)
            else:
                records.append(item)
            # print(item)
            # 5. 命中 & 过滤分别保存到不同文件。可以通过浏览过滤文件确保没有漏掉有用信息 #
            with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_record.json'), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(records,ensure_ascii=False, indent=4))
            with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_moneyfund.json'), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(money_funds,ensure_ascii=False, indent=4))
            with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_other.json'), 'w+', encoding='utf-8') as f:
                f.write(json.dumps(others, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    pass