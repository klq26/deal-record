# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
import ssl

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import pandas as pd

from login.requestHeaderManager import requestHeaderManager
from database.fundDBHelper import fundDBHelper

class qiemanSpider:

    def __init__(self, strategy = 'klq'):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        if strategy == 'klq':
            self.owner = '康力泉'
            self.headers = requestHeaderManager().getQiemanKLQ()
            # S 定投
            # totalElements: 16 # totalPages: 2
            plan150_id = u'CA8UKLYHA67WPK'
            # 150 补充
            # totalElements: 19 # totalPages: 2
            planS_id = u'CA8FCJKFPANTP2'
            self.plan_list = [{'name': '150份', 'value': plan150_id}, {'name': 'S定投', 'value': planS_id}]
        elif strategy == 'ksh':
            self.owner = '康世海'
            self.headers = requestHeaderManager().getQiemanKSH()
            # 稳稳的幸福
            wenwen = u'CA942R8128PFE7'
            self.plan_list = [{'name': '稳稳的幸福', 'value': wenwen}]
        # 交易详情 url 数组（后续逐个解析）
        self.detailUrlList = []
        self.results = []

    def get(self):
        print('且慢：{0} 获取中..'.format(self.owner))
        db = fundDBHelper()
        index = 0
        all_model_keys = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'note']
        # 取 500 条
        for plan in self.plan_list:
            folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
            if not os.path.exists(folder):
                os.makedirs(folder)
            tradelist_file = os.path.join(folder, '{0}_tradelist.json'.format(plan['name']))
            if not os.path.exists(tradelist_file):
                # 且慢他们家是从 page=0 开始的
                deal_list_url = 'https://qieman.com/pmdj/v2/orders?capitalAccountId={0}&page=0&size=500'.format(plan['value'])
                # 获取所有的成交记录概述
                response = requests.get(deal_list_url, headers = self.headers, verify=False)
                if response.status_code == 200:
                    with open(tradelist_file, 'w+', encoding='utf-8') as f:
                        f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                else:
                    print(response.status_code)
            # 读取该计划的列表
            with open(tradelist_file, 'r', encoding='utf-8') as f:
                datalist = json.loads(f.read())['content']
                detail_url = u'https://qieman.com/pmdj/v2/orders/{0}'
                folder = os.path.join(self.folder, 'debug', self.owner, 'detail')
                if not os.path.exists(folder):
                    os.makedirs(folder)
                for item in datalist:
                    # "orderProdType": "PO",
                    # "orderId": "PO202003199FANFSMAQIUR",
                    # "capitalAccountId": "CA8UKLYHA67WPK",
                    # "acceptTime": 1584597855000,
                    # "txnDay": 1584547200000,
                    # "confirmStatus": "P2",
                    # "uiConfirmStatusName": "确认成功",
                    # "payStatus": "2",
                    # "uiPayStatusName": "扣款成功",
                    # "orderCode": "P11",
                    # "capitalDirection": "IN",
                    # "uiOrderCodeName": "执行计划",
                    # "orderStatus": "SUCCESS",
                    # "uiOrderStatusName": "成功",
                    # "uiAmount": 1334,
                    # "po": {
                    #     "poCode": "LONG_WIN",
                    #     "poName": "长赢指数投资计划-150份"
                    # },
                    # "uiOrderDesc": "已于2020年3月23日完成",
                    # "hasDetail": true,
                    # "umaId": 10209,
                    # "umaName": "10万补充ETF计划",
                    # "orderUrl": "https://qieman.com/orders/PO202003199FANFSMAQIUR",
                    # "capitalAccountName": "长赢指数投资计划-150份"
                    unix_ts = int(int(item['acceptTime'])/1000)
                    dateObj = datetime.fromtimestamp(unix_ts)
                    date = str(dateObj)[0:10]
                    order_id = item['orderId']
                    detail_file = os.path.join(folder, '{0}_{1}_{2}_{3}.json'.format(date, item['umaName'], item['uiOrderCodeName'], item['uiOrderStatusName']))
                    if not os.path.exists(detail_file):
                        # 请求
                        response = requests.get(detail_url.format(order_id), headers = self.headers, verify=False)
                        if response.status_code == 200:
                            with open(detail_file, 'w+', encoding='utf-8') as f:
                                f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                    # 读取数据
                    with open(detail_file, 'r', encoding='utf-8') as f:
                        jsonData = json.loads(f.read())
                        plan_name = jsonData['po']['poName']
                        orders = jsonData['compositionOrders']
                        # 遍历每一条记录
                        for order in orders:
                            index = index + 1
                            # id
                            all_model_values = [index]
                            # date
                            unix_ts = int(int(item['acceptTime'])/1000)
                            dateObj = datetime.fromtimestamp(unix_ts)
                            date = str(dateObj)[0:10]
                            hour = dateObj.hour
                            all_model_values.append(date)
                            all_model_values.append(order['fund']['fundCode'])
                            all_model_values.append(order['fund']['fundName'])
                            confirm_amount = order['uiAmount']
                            confirm_volume = order['uiShare']
                            fee = order['fee']
                            occurMoney = order['uiAmount']
                            nav_unit = 0.0
                            nav_acc = 0.0
                            opType = order['uiOrderCodeName']
                            if u'分红' in opType:
                                all_model_values.append('分红')
                                occurMoney = confirm_amount
                                db_record = db.selectNearestDividendDateFundNav(code = all_model_values[2], date = all_model_values[1])
                                nav_unit = db_record[1]
                                nav_acc = db_record[2]
                                all_model_values.append(nav_unit)
                                all_model_values.append(nav_acc)
                            else:
                                db_record = None
                                if hour >= 15:
                                    # 超过15点，净值应该按下一个交易日算
                                    # 注意：目前发现只有且慢给回的信息是这样的。蛋卷给回的都是 00:00:00 的时间戳
                                    db_record = db.selectFundNavAfterDate(code = all_model_values[2], date = all_model_values[1])
                                else:
                                    db_record = db.selectFundNavByDate(code = all_model_values[2], date = all_model_values[1])
                                nav_acc = db_record[2]
                                # 如果是 01-01 这样节日下单，日期应该换成有效交易日，即顺延的下一天
                                all_model_values[1] = db_record[0]
                                if u'买' in opType or u'申' in opType or u'转换至' in opType:
                                    all_model_values.append('买入')
                                    confirm_amount = round(occurMoney - fee, 2)
                                elif u'赎' in order['uiOrderCodeName']:
                                    all_model_values.append('卖出')
                                    confirm_amount = round(occurMoney + fee, 2)
                                else:
                                    print('未知操作：{0}'.format(opType))
                                    all_model_values.append(opType)
                                all_model_values.append(order['nav'])
                                all_model_values.append(nav_acc)
                            all_model_values.append(confirm_volume)
                            all_model_values.append(confirm_amount)
                            all_model_values.append(fee)
                            all_model_values.append(occurMoney)
                            all_model_values.append(self.owner)
                            all_model_values.append(plan_name + '_' + order['orderId'])
                            itemDict = dict(zip(all_model_keys, all_model_values))
                            self.results.append(itemDict)
        # 日期升序，重置 id
        self.results.sort(key=lambda x: x['date'])
        for i in range(1, len(self.results) + 1):
            self.results[i-1]['id'] = i
        # [print(x) for x in self.results]
        # 写入文件
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(self.results, ensure_ascii = False, indent = 4))
        return self.results

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
            df.to_csv(os.path.join(self.folder, 'output', '{0}-qieman-unique-codes.csv'.format(self.owner)), sep='\t')
            return df

if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'ksh\'：康世海')
        exit()
    # 传入配置，开始流程
    spider = qiemanSpider(strategy = strategy)
    spider.get()