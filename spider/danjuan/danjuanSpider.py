# -*- coding: utf-8 -*-

import os
import sys
import math
import json
from datetime import datetime
import ssl

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import pandas as pd

from login.requestHeaderManager import requestHeaderManager
from category.categoryManager import categoryManager
from database.fundDBHelper import fundDBHelper

global_name = '蛋卷'

class danjuanSpider:

    def __init__(self, strategy = 'klq'):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.categoryManager = categoryManager()
        if strategy == 'klq':
            self.owner = '康力泉'
            self.headers = requestHeaderManager().getDanjuanKLQ()
        elif strategy == 'lsy':
            self.owner = '李淑云'
            self.headers = requestHeaderManager().getDanjuanLSY()
        elif strategy == 'ksh':
            self.owner = '康世海'
            self.headers = requestHeaderManager().getDanjuanKSH()
        # 交易详情 url 数组（后续逐个解析）
        self.detailUrlList = []
        self.results = []

    # 获取数据
    def get(self):
        print('蛋卷：{0} 获取中..'.format(self.owner))
        db = fundDBHelper()
        deal_list_url = u'https://danjuanapp.com/djapi/order/p/list?page=1&size=2000&type=all'
        # 获取所有的成交记录概述
        response = requests.get(deal_list_url, headers = self.headers, verify=False)
        folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
        if not os.path.exists(folder):
            os.makedirs(folder)
        tradelist_file = os.path.join(folder, 'tradelist.json')
        if not os.path.exists(tradelist_file):
            if response.status_code == 200:
                folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
                with open(tradelist_file, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
            else:
                print(response.status_code)
        # 请求每一条详情(仅包含“交易成功”，忽略“撤单”，“交易进行中” 等非确定情况)
        all_model_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', 'note']
        index = 0
        with open(tradelist_file, 'r', encoding='utf-8') as f:
            jsonData = json.loads(f.read())
            datalist = jsonData['data']['items']
            detail_url = u'https://danjuanapp.com/djapi/order/p/plan/{0}'
            # 这个是专门为了去拿一下确认净值的，其他信息 detail_url 都有了
            nav_detail_url = u'https://danjuanapp.com/djapi/plan/order/{0}'
            folder = os.path.join(self.folder, 'debug', self.owner, 'detail')
            if not os.path.exists(folder):
                os.makedirs(folder)
            for item in datalist:
                # "order_id": "1819139915911312513",
                # "code": "CSI1019",
                # "name": "钉钉宝365天组合",
                # "status_desc": "交易成功",
                # "action_desc": "卖出",
                # "created_at": 1584584824274,
                # "title": "钉钉宝365天组合",
                if item['status_desc'] != '交易成功':
                    print('忽略非正常交易：{0}\n{1}\n'.format(item['status_desc'], item))
                    continue
                unix_ts = int(int(item['created_at'])/1000)
                date = str(datetime.fromtimestamp(unix_ts))[0:10]
                # order_id = item['order_id']
                detail_file = os.path.join(folder, '{0}_{1}_{2}_{3}_{4}.json'.format(date, item['name'], item['action_desc'], item['status_desc'], item['order_id']))
                # 获取每一笔已成功的成交数据
                if not os.path.exists(detail_file):
                    response = requests.get(detail_url.format(item['order_id']), headers = self.headers, verify=False)
                    if response.status_code == 200:
                        with open(detail_file, 'w+', encoding='utf-8') as f:
                            f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                            jsonData = json.loads(response.text)
                else:
                    with open(detail_file, 'r', encoding='utf-8') as f:
                        try:
                            jsonData = json.loads(f.read())['data']
                            # 注意：这里会忽略如南方天天利B 这种货币基金的买入和分红
                            if jsonData['status'] != 'success' or 'sub_order_list' not in jsonData.keys():
                                print('忽略：{0}'.format(detail_file))
                                continue
                            orderlist = jsonData['sub_order_list'][0]['orders']
                            for order in orderlist:
                                if '货币' in order['fd_name']:
                                    # 暂时不收集货币基金操作
                                    print('忽略：{0}'.format(detail_file))
                                    continue

                                # "plan_name": "螺丝钉指数基金组合",
                                # "fd_code": "003318",
                                # "fd_name": "景顺长城中证500低波动",
                                # "title": "景顺长城中证500低波动",
                                # "action_desc": "买入",
                                # "status_desc": "交易成功",
                                # "type": "plan",
                                # "action": "022",
                                # "status": "success",
                                # "ts": 1553616000000,
                                # "confirm_ts": 1553702400000,
                                # "amount": 85.13,
                                # "volume": 0,
                                # "confirm_amount": 85.13,
                                # "confirm_volume": 84.57,
                                # "fee": 0.1,
                                # "value_desc": "85.13元",
                                # "value_text": "下单金额",
                                # "confirm_value_text": "确认份额",
                                # "confirm_value_desc": "84.57份",
                                # "bank_name": "招商银行(6292)",
                                # "order_id": "1978041789057135658"
                                # 买入
                                # nav = (confirm_amount - fee) / confirm_volume
                                # 卖出
                                # nav = (confirm_amount + fee) / confirm_volume
                                index = index + 1
                                # id
                                all_model_values = [index]
                                # date
                                unix_ts = int(int(order['ts'])/1000)
                                all_model_values.append(str(datetime.fromtimestamp(unix_ts))[0:10])
                                all_model_values.append(order['fd_code'])
                                all_model_values.append(order['fd_name'])
                                confirm_amount = order['confirm_amount']
                                confirm_volume = order['confirm_volume']
                                fee = order['fee']
                                occurMoney = 0
                                opType = order['action_desc']
                                nav_unit = 0.0
                                nav_acc = 0.0
                                all_model_values.append(opType)
                                if opType == '分红':
                                    occurMoney = confirm_amount
                                    db_record = db.selectNearestDividendDateFundNav(code = all_model_values[2], date = all_model_values[1])
                                    nav_unit = db_record[1]
                                    nav_acc = db_record[2]
                                    all_model_values.append(nav_unit)
                                else:
                                    # 净值
                                    db_record = db.selectFundNavByDate(code = all_model_values[2], date = all_model_values[1])
                                    nav_unit = db_record[1]
                                    nav_acc = db_record[2]
                                    all_model_values.append(nav_unit)
                                    if order['action_desc'] == '买入':
                                        occurMoney = round(confirm_amount + fee, 2)
                                    elif order['action_desc'] == '卖出':
                                        occurMoney = round(confirm_amount - fee, 2)
                                    else:
                                        continue
                                all_model_values.append(nav_acc)
                                all_model_values.append(confirm_volume)
                                all_model_values.append(confirm_amount)
                                all_model_values.append(fee)
                                all_model_values.append(occurMoney)
                                all_model_values.append(self.owner + '_' + global_name + '_' + order['plan_name'])
                                categoryInfo = self.categoryManager.getCategory(all_model_values[2])
                                if categoryInfo != {}:
                                    all_model_values.append(categoryInfo['category1'])
                                    all_model_values.append(categoryInfo['category2'])
                                    all_model_values.append(categoryInfo['category3'])
                                    all_model_values.append(categoryInfo['categoryId'])
                                all_model_values.append(order['plan_name'] + '_' + order['order_id'])
                                itemDict = dict(zip(all_model_keys, all_model_values))
                                self.results.append(itemDict)
                        except Exception as e:
                            print('Exception: {0}'.format(jsonData))
                            print(e)
        # 日期升序，重置 id
        self.results.sort(key=lambda x: x['date'])
        for i in range(1, len(self.results) + 1):
            self.results[i-1]['id'] = i
        # [print(x) for x in self.results]
        # 写入文件
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(self.results, ensure_ascii = False, indent = 4))

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
            df.to_csv(os.path.join(self.folder, 'output', '{0}-danjuan-unique-codes.csv'.format(self.owner)), sep='\t')
            return df

    def load(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'lsy\'：李淑云 \'ksh\'：康世海')
        exit()
    # 传入配置，开始流程
    spider = danjuanSpider(strategy = strategy)
    spider.get()


