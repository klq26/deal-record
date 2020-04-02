# -*- coding: utf-8 -*-
import os
import sys
import json

import pandas as pd
import numpy as np

from category.categoryManager import categoryManager
from spider.huatai.huataiHistory import huataiHistory

# NOTE：取值是 “资金流水”
global_name = '华泰证券'

# 0. 定义预期数据。所有 suppose 开头的变量都是需要验证的内容。当与预期不符时，程序应该报错并终止 #

# 预期文件的全部列名（第一次是从 xlsx 中复制过来的）
suppose_all_file_columns = ['流水号', '发生日期', '业务名称', '发生金额', '剩余金额', '币种', '股东代码', '证券代码', '证券名称', '买卖标志', '成交价格', '成交数量', '备注', '佣金', '印花税', '过户费', '其他费']
# 我们实际需要的列名
suppose_needed_columns=['流水号', '发生日期', '业务名称', '证券代码', '证券名称', '买卖标志', '成交价格', '成交数量', '发生金额', '佣金', '印花税', '过户费', '其他费','备注']
# 证券代码取值范围
suppose_codes = {'name': '证券代码', 'value': ['510050', ' ', '510300', '510500', '159915', '518880', '159938']}
# 证券名称取值范围
suppose_names = {'name': '证券名称', 'value': ['50ETF', ' ', '300ETF', '500ETF', '创业板', '黄金ETF', '医药']}
# 委托类别取值范围
suppose_operates = {'name': '买卖标志', 'value': ['卖出']}
# 业务名称取值范围
suppose_bussiness_name = {'name': '业务名称', 'value': ['股息入帐', '基金资金拨出', '基金资金拨入', '银行转取', '利息归本', '证券卖出', '资管转让资金上账']}
# 需要校验的列集合
suppose_justify_columns = [suppose_codes, suppose_names, suppose_operates, suppose_bussiness_name]

class huataiSpider:

    def __init__(self):
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.owner = u'康力泉'
        self.categoryManager = categoryManager()
        # TEST 显示列名，列唯一值
        # df = pd.read_excel(os.path.join(self.folder, 'input', global_name + u'.xlsx'))
        # file_columns = df.columns
        # # 列名
        # print(list(file_columns))
        # # 列唯一值
        # for cate in df.columns:
        #     print("{" + "'name': '{0}', 'value': [{1}]".format(cate, ', '.join(["'{0}'".format(x) for x in df[cate].unique()])) + "}")
        # exit(1)
        
        # 1. 读取文件并校验目标文件的列名是否符合预期 #
        df = pd.read_excel(os.path.join(self.folder, 'input', global_name + u'.xlsx'))
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
        needed_df['fee'] = needed_df['佣金'] + needed_df['印花税'] + needed_df['过户费'] + needed_df['其他费']
        needed_df.drop(columns=['佣金', '印花税','过户费','其他费'])
        needed_df['occurMoney'] = needed_df['发生金额']
        needed_df['account'] = global_name
        needed_df['category1'] = '无'
        needed_df['category2'] = '无'
        needed_df['category3'] = '无'
        needed_df['categoryId'] = 1
        # 5. 生成 json 对象
        # 按 model key 值顺序重组 dataframe
        reindex_columns=['流水号', '发生日期', '证券代码', '证券名称', '买卖标志', '成交价格', 'nav_acc', '成交数量', '发生金额', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', '备注']
        needed_df = needed_df.reindex(columns=reindex_columns)
        # print(needed_df)
        return needed_df

    def get(self):
        # 模型字段数组
        all_model_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', 'note']
        records = []
        moneyfunds = []
        others = []
        for x in self.needed_df.values:
            item = dict(zip(all_model_keys, list(x)))
            # 最后一次修改
            item['date'] = '{0}-{1}-{2}'.format(str(item['date'])[0:4],str(item['date'])[4:6],str(item['date'])[6:8])
            item['code'] = str(item['code'])
            # if item['dealType'] == '基金申购':
            #     item['dealType'] = '买入'
            if item['dealType'] == '买入':
                item['occurMoney'] = item['dealMoney'] + item['fee']
            elif item['dealType'] == '卖出':
                # 华泰证券里面，发生金额是到手金额，所以总流水应该是 deal + fee
                item['dealMoney'] = item['occurMoney'] + item['fee']
            if '股息入账' in item['note']:
                item['dealType'] = '分红'
            item['volume'] = abs(item['volume'])
            item['occurMoney'] = round(item['occurMoney'], 2)
            item['dealMoney'] = round(item['dealMoney'], 2)
            # 非交易性操作
            if item['code'] == ' ' or item['name'] == ' ':
                others.append(item)
            else:
                categoryInfo = self.categoryManager.getCategory(item['code'])
                if categoryInfo != {}:
                    item['category1'] = categoryInfo['category1']
                    item['category2'] = categoryInfo['category2']
                    item['category3'] = categoryInfo['category3']
                    item['categoryId'] = categoryInfo['categoryId']
                records.append(item)
            # print(item)

        # 5. 加载历史
        history = huataiHistory()
        history.get()
        with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_record.json'), 'r', encoding='utf-8') as f:
            history_records = json.loads(f.read())
            [records.append(x) for x in history_records]
            # 日期升序，重置 id
            records.sort(key=lambda x: x['date'])
            for i in range(1, len(records) + 1):
                records[i-1]['id'] = i

        with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_moneyfund.json'), 'r', encoding='utf-8') as f:
            history_moneyfunds = json.loads(f.read())
            [moneyfunds.append(x) for x in history_moneyfunds]
            # 日期升序，重置 id
            moneyfunds.sort(key=lambda x: x['date'])
            for i in range(1, len(moneyfunds) + 1):
                moneyfunds[i-1]['id'] = i
            
        with open(os.path.join(self.folder, 'output', global_name + u'2015-2019_other.json'), 'r', encoding='utf-8') as f:
            history_others = json.loads(f.read())
            [others.append(x) for x in history_others]
            # 日期升序，重置 id
            others.sort(key=lambda x: x['date'])
            for i in range(1, len(others) + 1):
                others[i-1]['id'] = i


        # 5. 命中 & 过滤分别保存到不同文件。可以通过浏览过滤文件确保没有漏掉有用信息 #
        with open(os.path.join(self.folder, 'output', u'康力泉' + u'_record.json'), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(records,ensure_ascii=False, indent=4))
        with open(os.path.join(self.folder, 'output', u'康力泉' + u'_moneyfund.json'), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(moneyfunds,ensure_ascii=False, indent=4))
        with open(os.path.join(self.folder, 'output', u'康力泉' + u'_other.json'), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(others, ensure_ascii=False, indent=4))
        return records
    
    # 获取所有记录中的唯一代码
    def uniqueCodes(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            datalist = json.loads(f.read())
            names = []
            codes = []
            for x in datalist:
                names.append(x['name'])
                codes.append(x['code'])
            df = pd.DataFrame()
            df['name'] = names
            df['code'] = codes
            df = df.drop_duplicates(['code'])
            df = df.sort_values(by='code' , ascending=True)
            df = df.reset_index(drop=True)
            df.to_csv(os.path.join(self.folder, 'output', '{0}-huatai-unique-codes.csv'.format(self.owner)), sep='\t')
            return df

    def load(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

if __name__ == "__main__":
    spider = huataiSpider()
    spider.get()