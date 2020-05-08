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
from category.categoryManager import categoryManager
from database.fundDBHelper import fundDBHelper
from database.dealRecordDBHelper import dealRecordDBHelper
from spider.common.dealRecordModel import *

global_name = '且慢'

class qiemanSpider:

    def __init__(self, strategy = 'klq'):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.categoryManager = categoryManager()
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
        self.results = []
        folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
        if not os.path.exists(folder):
            os.makedirs(folder)
        # tradelist.json 存放位置
        self.tradelistfolder = folder
        folder = os.path.join(self.folder, 'debug', self.owner, 'detail')
        if not os.path.exists(folder):
            os.makedirs(folder)
        # traderecords 文件存放位置
        self.detailfolder = folder
        self.current_plan = None

    def get(self, forceUpdate = False):
        print('且慢：{0} 获取中..'.format(self.owner))
        # 取 500 条
        for plan in self.plan_list:
            self.current_plan = plan
            tradelist_file = os.path.join(self.tradelistfolder, '{0}_tradelist.json'.format(plan['name']))
            # 准备成交记录列表
            tradelistJson = self._prepareTradelist(plan = plan, path = tradelist_file, forceUpdate = forceUpdate)
            datalist = tradelistJson['content']
            # 从 tradelist.json 列表中，请求每一次的交易详情(仅包含“交易成功”，忽略“撤单”，“交易进行中” 等非确定情况)
            for tradeRecord in datalist:
                dealRecordsJson = self._prepareTradeRecord(tradeRecord)
                dealRecords = self._prepareDealRecords(dealRecordsJson)
                [self.results.append(x) for x in dealRecords]
        if os.path.exists(os.path.join(self.folder, 'input', '{0}_addition.json'.format(self.owner))):
            # 注意：且慢网站目前不公布跟计划品种分红的交易，暂时只能自己补充，这点自己补齐，已和客服沟通过得到确认
            # 另外，父亲的组合转换，只有一笔转换。实际上应该是一笔买入 + 一笔卖出。程序里，转换只提现了买入。所以 addition 则补足基金的卖出部分
            input_path = os.path.join(self.folder, 'input', '{0}_addition.json'.format(self.owner))
            with open(input_path, 'r', encoding='utf-8') as f:
                dividends = json.loads(f.read())
                [self.results.append(x) for x in dividends]
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

    # 增量更新
    def increment(self):
        # 校验数据库和本地 json 文件是否完全匹配
        self.verifyHistoryData()
        json_datalist = self.load()
        json_datalist_count = len(json_datalist)
        # 新数据起始 id
        startId = json_datalist_count + 1
        startDate = datetime.strptime(json_datalist[-1]['date'], '%Y-%m-%d')
        print('且慢：{0} 增量更新中..'.format(self.owner))
        # 准备成交记录列表
        increments = []
        # 取 500 条
        for plan in self.plan_list:
            self.current_plan = plan
            tradelist_file = os.path.join(self.tradelistfolder, '{0}_tradelist.json'.format(plan['name']))
            # 准备成交记录列表
            tradelistJson = self._prepareTradelist(plan = plan, path = tradelist_file, forceUpdate = True)
            datalist = tradelistJson['content']
            # 从 tradelist.json 列表中，请求每一次的交易详情(仅包含“交易成功”，忽略“撤单”，“交易进行中” 等非确定情况)
            for tradeRecord in datalist:
                dealRecordsJson = self._prepareTradeRecord(tradeRecord, startDate = startDate)
                dealRecords = self._prepareDealRecords(dealRecordsJson)
                [increments.append(x) for x in dealRecords]
        # 日期升序，重置 id
        increments.sort(key=lambda x: x['date'])
        for i in range(0, len(increments)):
            increments[i]['id'] = i + startId
        # [print(x) for x in increments]
        [json_datalist.append(x) for x in increments]
        # 写入文件
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(json_datalist, ensure_ascii = False, indent = 4))

    # 检测项目中 record.json 文件的数据和数据库数据是否一致
    def verifyHistoryData(self):
        db = dealRecordDBHelper()
        tablename = ''
        account = ''
        if self.owner == u'康力泉':
            tablename = u'klq'
            account = u'且慢'
        elif self.owner == u'康世海':
            tablename = u'parents'
            account = u'康世海_且慢'
        # 数据库数据
        df = db.selectAllRecordsToDataFrame(tablename = tablename, account = account)
        keys = list(df.columns)
        db_datalist = []
        for x in list(df.values):
            db_datalist.append(dict(zip(keys, x)))
        db_datalist_count = len(db_datalist)
        # 本地数据
        json_datalist = self.load()
        json_datalist_count = len(json_datalist)
        # 校验数据数量
        if db_datalist_count != json_datalist_count:
            print('[ERROR] qiemanSpider 数据库校验失败：个数不统一。数据库：{0} 本地：{1}'.format(db_datalist_count, json_datalist_count))
            exit(1)
        # 校验每条数据关键字段
        checkEqual = lambda x, y : x['date'] == y['date'] and x['code'] == y['code'] and x['dealType'] == y['dealType'] and x['nav_unit'] == y['nav_unit'] and x['volume'] == y['volume'] and x['occurMoney'] == y['occurMoney'] and x['note'] == y['note']
        checkResults = list(map(checkEqual, db_datalist, json_datalist))
        if False in checkResults:
            index = checkResults.index(False)
            print('[ERROR] qiemanSpider 数据库校验失败：数据不匹配。\n\n数据库：\n{0} \n\n本地：\n{1}'.format(db_datalist[index], json_datalist[index]))
            exit(1)
        else:
            # print(checkResults, len(checkResults))
            print('[SUCCESS] qiemanSpider {0} 历史数据校验通过'.format(self.owner))

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

    def load(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    ########################################################################
    # private methods
    ########################################################################

    # 准备交易列表 json 数据
    def _prepareTradelist(self, plan, path, forceUpdate = False):
        # 且慢他们家是从 page=0 开始的
        deal_list_url = 'https://qieman.com/pmdj/v2/orders?capitalAccountId={0}&page=0&size=500'.format(plan['value'])
        # 获取所有的成交记录概述
        if forceUpdate:
            response = requests.get(deal_list_url, headers=self.headers, verify=False)
            if response.status_code == 200 and response.text != u'':
                with open(path, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                    return json.loads(response.text)
            else:
                print('[ERROR] qiemanSpider {0}_tradelist.json 获取失败 code:{1} text:{2}'.format(plan['name'], response.status_code, response.text))
                if not os.path.exists(path):
                    print('[ERROR] qiemanSpider {0}_tradelist.json 缺失，退出'.format(plan['name']))
                    exit(1)
                else:
                    with open(path, 'r', encoding='utf-8') as f:
                        jsonData = json.loads(f.read())
                        return jsonData
        else:
            if not os.path.exists(path):
                print('[ERROR] qiemanSpider {0}_tradelist.json 缺失，退出'.format(plan['name']))
                exit(1)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    jsonData = json.loads(f.read())
                    return jsonData

    # 根据 tradelist.json 中的数组，准备每一条交易详情数据
    def _prepareTradeRecord(self, item, startDate = None):
        detail_url = u'https://qieman.com/pmdj/v2/orders/{0}'
        unix_ts = int(int(item['acceptTime'])/1000)
        # startDate
        tradeDate = datetime.fromtimestamp(unix_ts)
        if startDate != None and isinstance(startDate, datetime):
            if startDate >= tradeDate:
                print('[Skip] qiemanSpider 忽略已入库交易。数据库最后记录时间：{0} 当前交易记录时间：{1}\n'.format(startDate, tradeDate))
                return json.loads('[]')
        date = str(tradeDate)[0:10]
        order_id = item['orderId']
        plan_name = item['po']['poName']
        detail_file = os.path.join(self.detailfolder, '{0}_{1}_{2}_{3}_{4}.json'.format(date, plan_name, item['uiOrderCodeName'], item['uiOrderStatusName'], item['orderId']))
        if not os.path.exists(detail_file):
            # 请求
            response = requests.get(detail_url.format(order_id), headers = self.headers, verify=False)
            if response.status_code == 200:
                with open(detail_file, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                    jsonData = json.loads(response.text)
                    return jsonData
            else:
                print('[ERROR] qiemanSpider {0} 获取失败 code:{1} text:{2}'.format(detail_file, response.status_code, response.text))
                if not os.path.exists(detail_file):
                    print('[ERROR] qiemanSpider {0} 缺失，退出'.format(detail_file))
                    exit(1)
        else:
            with open(detail_file, 'r', encoding='utf-8') as f:
                jsonData = json.loads(f.read())
                return jsonData
        pass

    # 根据 trade detail.json 中的数组，准备每一条成交记录
    def _prepareDealRecords(self, jsonData):
        db = fundDBHelper()
        all_model_keys = dealRecordModelKeys()
        index = 0
        results = []
        # 遍历每一条记录
        orders = jsonData['compositionOrders']
        for order in orders:
            opType = order['uiOrderCodeName']
            index = index + 1
            # id
            all_model_values = [index]
            # date
            unix_ts = int(int(order['acceptTime'])/1000)
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
                if u'买' in opType or u'申' in opType:
                    all_model_values.append('买入')
                    confirm_amount = round(occurMoney - fee, 2)
                elif u'赎' in opType:
                    all_model_values.append('卖出')
                    confirm_amount = round(occurMoney + fee, 2)
                elif u'转换至' in opType:
                    # 把且慢稳稳的幸福的转换至都分拆放到 addition.json 里面了，这块太难搞了，以后应该也不会买且慢组合了，就不写逻辑了。
                    print('\n[WARNING] qiemanSpider 且慢的转换至应该是一笔交易转两笔，请自行确认是否再 addition.json 中做了人工补充。\n\n{0}\n'.format(order))
                    continue
                else:
                    print('[WARNING] qiemanSpider 未知操作：{0}'.format(opType))
                    all_model_values.append(opType)
                all_model_values.append(order['nav'])
                all_model_values.append(nav_acc)
            all_model_values.append(confirm_volume)
            all_model_values.append(confirm_amount)
            all_model_values.append(fee)
            all_model_values.append(occurMoney)
            all_model_values.append(self.owner + '_' + global_name + '_' + self.current_plan['name'])
            categoryInfo = self.categoryManager.getCategoryByCode(all_model_values[2])
            if categoryInfo != {}:
                all_model_values.append(categoryInfo['category1'])
                all_model_values.append(categoryInfo['category2'])
                all_model_values.append(categoryInfo['category3'])
                all_model_values.append(categoryInfo['categoryId'])
            all_model_values.append('https://qieman.com/orders/' + jsonData['orderId'] + '子编号：' + order['orderId'])
            itemDict = dict(zip(all_model_keys, all_model_values))
            results.append(itemDict)
        return results

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