# -*- coding: utf-8 -*-
import os
import sys
import json

import pandas as pd
import numpy as np

from dealRecordModel import dealRecordModel


# NOTE：取值是 “历史成交”

global_name = '华宝证券'

# TEST 显示列名，列唯一值
# df = pd.read_excel(os.path.join(os.getcwd(),'data', global_name + u'.xlsx'))
# file_columns = df.columns
# # 列名
# print(list(file_columns))
# # 列唯一值
# for cate in df.columns:
#     print("{" + "'name': '{0}', 'value': [{1}]".format(cate, ', '.join(["'{0}'".format(x) for x in df[cate].unique()])) + "}")
# exit(1)

# 0. 定义预期数据。所有 suppose 开头的变量都是需要验证的内容。当与预期不符时，程序应该报错并终止 #

# 预期文件的全部列名（第一次是从 xlsx 中复制过来的）
suppose_all_file_columns = ['成交日期', '成交时间', '股东代码', '证券代码', '证券名称', '委托类别', '成交价格', '成交数量', '发生金额', '剩余金额', '佣金', '印花税', '过户费', '成交费', '成交编号', '委托编号']
# 我们实际需要的列名
suppose_needed_columns=['成交编号', '成交日期', '证券代码', '证券名称', '委托类别', '成交价格', '成交数量', '发生金额', '佣金', '印花税', '过户费', '成交费']
# 证券代码取值范围
suppose_codes = {'name': '证券代码', 'value': ['799999', '162411', '515180', '159920', '513520', '160416']}
# 证券名称取值范围
suppose_names = {'name': '证券名称', 'value': ['登记指定', '华宝油气', '100红利', '恒生ETF', '日经ETF', '石油基金']}
# 委托类别取值范围
suppose_operates = {'name': '委托类别', 'value': ['指定', '买入', '卖出', '基金申购']}
# 需要校验的列集合
suppose_justify_columns = [suppose_codes, suppose_names, suppose_operates]

# 1. 读取文件并校验目标文件的列名是否符合预期 #

df = pd.read_excel(os.path.join(os.getcwd(), 'data', global_name + u'.xlsx'))
file_columns = df.columns

is_columns_equals = file_columns == suppose_all_file_columns
for x in range(0,len(is_columns_equals)):
    if is_columns_equals[x] == False:
        print(global_name + '原始数据列名有误：{0} 预期：{1} vs 实际：{2}'.format(x, suppose_all_file_columns[x], file_columns[x]))
        exit(1)
        break
print('列名 校验通过')

# 2. 取目标列 #

needed_df = pd.DataFrame(df, columns=suppose_needed_columns)

# 3. 校验特殊列的合法性 #

for columnDict in suppose_justify_columns:
    target_column_values = needed_df[columnDict['name']].unique()
    for value in target_column_values:
        if str(value) not in columnDict['value']:
            print(global_name + '原始数据列值有误，目标值：{0} 不在列：{1} 的预期值之中。'.format(value, columnDict['name']))
            exit(1)
    print('{0} 校验通过'.format(columnDict['name']))

# 4. 调整（增删改查） dataframe 数据列 #

needed_df['nav_acc'] = needed_df['成交价格']
needed_df['fee'] = needed_df['佣金'] + needed_df['印花税'] + needed_df['过户费'] + needed_df['成交费']
needed_df.drop(columns=['佣金', '印花税','过户费','成交费'])
needed_df['occurMoney'] = needed_df['发生金额']
needed_df['note'] = 'NA'
needed_df['account'] = global_name

# 5. 生成 json 对象

# 按 model key 值顺序重组 dataframe
reindex_columns=['成交编号', '成交日期', '证券代码', '证券名称', '委托类别', '成交价格', 'nav_acc', '成交数量', '发生金额', 'fee','occurMoney','account','note']
needed_df = needed_df.reindex(columns=reindex_columns)
# print(needed_df)
# 模型字段数组
all_model_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'note']
records = []
others = []
for x in needed_df.values:
    item = dict(zip(all_model_keys, list(x)))
    # 最后一次修改
    item['date'] = '{0}/{1}/{2}'.format(str(item['date'])[0:4],str(item['date'])[4:6],str(item['date'])[6:8])
    if item['dealType'] == '基金申购':
        item['dealType'] = '买入'
    if item['dealType'] == '买入':
        item['occurMoney'] = item['dealMoney'] + item['fee']
    elif item['dealType'] == '卖出':
        item['occurMoney'] = item['dealMoney'] - item['fee']
    item['occurMoney'] = round(float(item['occurMoney']), 2)
    if item['dealType'] in ['买入','卖出']:
        records.append(item)
    else:
        others.append(item)
    # print(item)


# 5. 命中 & 过滤分别保存到不同文件。可以通过浏览过滤文件确保没有漏掉有用信息 #

with open(os.path.join(os.getcwd(), 'data', global_name + u'_record.json'), 'w+', encoding='utf-8') as f:
    f.write(json.dumps(records,ensure_ascii=False, indent=4))

with open(os.path.join(os.getcwd(), 'data', global_name + u'_other.json'), 'w+', encoding='utf-8') as f:
    f.write(json.dumps(others, ensure_ascii=False, indent=4))
