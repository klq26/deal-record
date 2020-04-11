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
from spider.common.dealRecordModel import *

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
        self.results = []
        folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
        if not os.path.exists(folder):
            os.makedirs(folder)
        # tradelist.json 存放位置
        self.tradelist_file = os.path.join(folder, 'tradelist.json')
        folder = os.path.join(self.folder, 'debug', self.owner, 'detail')
        if not os.path.exists(folder):
            os.makedirs(folder)
        # traderecords 文件存放位置
        self.detailfolder = folder

    # 获取数据
    def get(self, forceUpdate = False):
        print('蛋卷：{0} 获取中..'.format(self.owner))
        # 准备成交记录列表
        tradelistJson = self._prepareTradelist(path = self.tradelist_file, forceUpdate = forceUpdate)
        datalist = tradelistJson['data']['items']
        # 从 tradelist.json 列表种，请求每一次的交易详情(仅包含“交易成功”，忽略“撤单”，“交易进行中” 等非确定情况)
        for tradeRecord in datalist:
            dealRecordsJson = self._prepareTradeRecord(tradeRecord)
            dealRecords = self._prepareDealRecords(dealRecordsJson)
            [self.results.append(x) for x in dealRecords]
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

    ########################################################################
    # private methods
    ########################################################################

    # 准备交易列表 json 数据
    def _prepareTradelist(self, path, forceUpdate = False):
        deal_list_url = u'https://danjuanapp.com/djapi/order/p/list?page=1&size=2000&type=all'
        # 获取所有的成交记录概述
        if forceUpdate:
            response = requests.get(deal_list_url, headers=self.headers, verify=False)
            if response.status_code == 200:
                with open(path, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                    return json.loads(response.text)
            else:
                print('[ERROR] danjuanSpider tradelist.json 获取失败 code:{0} text:{1}'.format(response.status_code, response.text))
                if not os.path.exists(path):
                    print('[ERROR] danjuanSpider tradelist.json 缺失，退出')
                    exit(1)
                else:
                    with open(path, 'r', encoding='utf-8') as f:
                        jsonData = json.loads(f.read())
                        return jsonData
        else:
            if not os.path.exists(path):
                print('[ERROR] danjuanSpider tradelist.json 缺失，退出')
                exit(1)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    jsonData = json.loads(f.read())
                    return jsonData

    # 根据 tradelist.json 中的数组，准备每一条交易详情数据
    def _prepareTradeRecord(self, item):
        if item == None:
            return json.loads('[]')
        detail_url = u'https://danjuanapp.com/djapi/order/p/plan/{0}'
        # model sample
        # "order_id": "1819139915911312513",
        # "code": "CSI1019",
        # "name": "钉钉宝365天组合",
        # "status_desc": "交易成功",
        # "action_desc": "卖出",
        # "created_at": 1584584824274,
        # "title": "钉钉宝365天组合",
        if item['status_desc'] != '交易成功':
            print('[Warning] danjuanSpider 忽略非正常交易详情：{0}\n{1}\n'.format(item['status_desc'], item))
            return json.loads('[]')
        unix_ts = int(int(item['created_at'])/1000)
        date = str(datetime.fromtimestamp(unix_ts))[0:10]
        # order_id = item['order_id']
        detail_file = os.path.join(self.detailfolder, '{0}_{1}_{2}_{3}_{4}.json'.format(date, item['name'], item['action_desc'], item['status_desc'], item['order_id']))
        # 获取每一笔已成功的成交数据（已存在的数据没有变化的就不用重新下载了，提高效率）
        if not os.path.exists(detail_file):
            response = requests.get(detail_url.format(item['order_id']), headers = self.headers, verify=False)
            if response.status_code == 200:
                with open(detail_file, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
                    jsonData = json.loads(response.text)
                    return jsonData['data']
            else:
                print('[ERROR] danjuanSpider {0} 获取失败 code:{1} text:{2}'.format(detail_file, response.status_code, response.text))
                if not os.path.exists(detail_file):
                    print('[ERROR] danjuanSpider {0} 缺失，退出'.format(detail_file))
                    exit(1)
        else:
            with open(detail_file, 'r', encoding='utf-8') as f:
                jsonData = json.loads(f.read())['data']
                return jsonData
    
    # 根据 trade detail.json 中的数组，准备每一条成交记录
    def _prepareDealRecords(self, jsonData):
        if not isinstance(jsonData, dict):
            return []
        try:
            tradeDetailOpType = jsonData['action_desc']
            # 注意：这里会忽略如南方天天利B 这种货币基金的买入和分红
            if jsonData['status'] != 'success':
                print('[Warning] danjuanSpider 忽略非正常交易记录：{0}\n{1}\n'.format(tradeDetailOpType, jsonData))
                return []
            elif 'sub_order_list' not in jsonData.keys() and '货币' not in jsonData['name']:
                # 属于单笔基金的买卖而非 plan 组合交易
                return self._handleFundBuySell(jsonData)
            elif (tradeDetailOpType == u'分红' or tradeDetailOpType == u'买入') and '货币' in jsonData['name']:
                # 暂时不收集货币基金的分红及买入操作，但是转换相当于买入，还是要的
                print('[Warning] danjuanSpider 忽略货币基金非转换交易记录：{0}\n{1}\n'.format(tradeDetailOpType, jsonData))
                return []
            elif tradeDetailOpType == u'转换':
                return self._handlePlanConvert(jsonData)
            else:
                return self._handlePlanBuySell(jsonData)
        except Exception as e:
            print('[Exception] danjuanSpider 解析 dealrecord 异常：{0}'.format(jsonData))
            print(e)
            exit(1)

    # 处理单笔基金的买入卖出操作
    def _handleFundBuySell(self, tradeDetailJson):
        # 单只基金无法在 order 页面查看手续费，需要进一步请求
        fund_detail_url = 'https://danjuanapp.com/djapi/fund/order/{0}'
        jsonData = {}
        response = requests.get(fund_detail_url.format(tradeDetailJson['order_id']), headers = self.headers, verify=False)
        if response.status_code == 200:
            jsonData = json.loads(response.text)
        else:
            print('[ERROR] danjuanSpider 单只基金交易记录 {0} 获取失败 code:{1} text:{2}'.format(tradeDetailJson['order_id'], response.status_code, response.text))
            print('[ERROR] danjuanSpider 单只基金交易记录 {0} 缺失，退出'.format(tradeDetailJson['order_id']))
            exit(1)
        results = []
        if len(jsonData.keys()) == 0 or u'data' not in jsonData.keys():
            return []
        else:
            order = jsonData['data']
            db = fundDBHelper()
            all_model_keys = dealRecordModelKeys()
            index = 1
            results = []
            opType = order['action_desc']
            # id
            all_model_values = [index]
            # date
            unix_ts = int(int(order['confirm_date'])/1000)
            all_model_values.append(str(datetime.fromtimestamp(unix_ts))[0:10])
            all_model_values.append(order['fd_code'])
            all_model_values.append(order['fd_name'])
            confirm_amount = order['confirm_amount']
            confirm_volume = order['confirm_volume']
            confirm_infos = order['confirm_infos']
            fee = 0.0
            if len(confirm_infos) > 0:
                infos = confirm_infos[0]
                if len(infos) > 0:
                    for i in range(len(infos)-1, 0, -1):
                        info = infos[i]
                        if u'手续费' in info:
                            # 手续费,0.04元
                            feeStr = info.replace('手续费,','').replace('元','')
                            fee = round(float(feeStr),2)
                            break
            occurMoney = 0
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
                db_record = db.selectFundNavBeforeDate(code = all_model_values[2], date = all_model_values[1])
                nav_unit = db_record[1]
                nav_acc = db_record[2]
                all_model_values[1] = db_record[0]
                all_model_values.append(nav_unit)
                if opType == '买入' or opType == '转换':
                    occurMoney = round(confirm_amount + fee, 2)
                elif opType == '卖出':
                    occurMoney = round(confirm_amount - fee, 2)
                else:
                    print('单只基金买入错误：{0}'.format(opType))
            all_model_values.append(nav_acc)
            all_model_values.append(confirm_volume)
            all_model_values.append(confirm_amount)
            all_model_values.append(fee)
            all_model_values.append(occurMoney)
            all_model_values.append(self.owner + '_' + global_name + '_' + order['order_type_name'])
            categoryInfo = self.categoryManager.getCategoryByCode(all_model_values[2])
            if categoryInfo != {}:
                all_model_values.append(categoryInfo['category1'])
                all_model_values.append(categoryInfo['category2'])
                all_model_values.append(categoryInfo['category3'])
                all_model_values.append(categoryInfo['categoryId'])
            all_model_values.append('https://danjuanapp.com/djmodule/trade-details?ordertype=fund&orderid=' + order['order_id'])
            itemDict = dict(zip(all_model_keys, all_model_values))
            results.append(itemDict)
            return results
    # 处理组合转换（包括货币基金转组合，组合内部互转等）
    def _handlePlanConvert(self, tradeDetailJson):
        # "action_text": "成分基金转换信息",
        # "action": "036",
        # "action_text": "成分基金转入信息",
        # "action": "037",
        # "action_text": "成分基金转出信息",
        # "action": "038",
        db = fundDBHelper()
        all_model_keys = dealRecordModelKeys()
        index = 0
        results = []
        sub_order_list = tradeDetailJson['sub_order_list']
        for sub_order in sub_order_list:
            actionType = ''
            actionText = sub_order['action_text']
            if u'转换' in actionText:
                # 目前知道的，叫转换的操作，只有货币基金买组合的情况
                actionType = u'转换'
            elif u'转入' in actionText:
                actionType = u'买入'
            elif u'转出' in actionText:
                actionType = u'卖出'
            else:
                print('[Error] danjuanSpider 未知的转换系操作：{0}'.format(actionText))
                exit(1)
            orderlist = sub_order['orders']
            for order in orderlist:
                opType = actionType
                index = index + 1
                # id
                all_model_values = [index]
                # date
                unix_ts = 0
                unix_ts = int(int(order['confirm_ts'])/1000)
                all_model_values.append(str(datetime.fromtimestamp(unix_ts))[0:10])
                if opType == u'买入':
                    all_model_values.append(order['fd_code'])
                    all_model_values.append(order['fd_name'])
                elif opType == u'转换':
                    all_model_values.append(order['target_fd_code'])
                    all_model_values.append(order['target_fd_name'])
                elif opType == '卖出':
                    all_model_values.append(order['fd_code'])
                    all_model_values.append(order['fd_name'])
                confirm_amount = order['confirm_amount']
                confirm_volume = order['confirm_volume']
                fee = order['fee']
                occurMoney = 0
                nav_unit = 0.0
                nav_acc = 0.0
                if opType == u'转换':
                    opType = u'买入'
                all_model_values.append(opType)
                # 净值
                db_record = None
                if opType == u'买入':
                    # 因为基金公司确认份额是 T+1 日，所以净值使用的 T 日的
                    db_record = db.selectFundNavBeforeDate(code = all_model_values[2], date = all_model_values[1])
                    # 日期改成净值确认日
                    all_model_values[1] = db_record[0]
                elif opType == '卖出':
                    db_record = db.selectFundNavBeforeDate(code = all_model_values[2], date = all_model_values[1])
                    # 日期改成净值确认日
                    all_model_values[1] = db_record[0]
                else:
                    print('[Error] danjuanSpider 未知的操作：{0}'.format(opType))
                    exit(1)
                    continue
                nav_unit = db_record[1]
                nav_acc = db_record[2]
                all_model_values.append(nav_unit)
                if opType == '买入':
                    occurMoney = round(confirm_amount + fee, 2)
                elif opType == '卖出':
                    occurMoney = round(confirm_amount - fee, 2)
                else:
                    continue
                all_model_values.append(nav_acc)
                all_model_values.append(confirm_volume)
                all_model_values.append(confirm_amount)
                all_model_values.append(fee)
                all_model_values.append(occurMoney)
                all_model_values.append(self.owner + '_' + global_name + '_' + tradeDetailJson['target_name'])
                categoryInfo = self.categoryManager.getCategoryByCode(all_model_values[2])
                if categoryInfo != {}:
                    all_model_values.append(categoryInfo['category1'])
                    all_model_values.append(categoryInfo['category2'])
                    all_model_values.append(categoryInfo['category3'])
                    all_model_values.append(categoryInfo['categoryId'])
                all_model_values.append('https://danjuanapp.com/djmodule/trade-details?ordertype=plan&orderid=' + order['order_id'])
                itemDict = dict(zip(all_model_keys, all_model_values))
                results.append(itemDict)
        return results

    # 处理正常的买卖交易
    def _handlePlanBuySell(self, tradeDetailJson):
        db = fundDBHelper()
        all_model_keys = dealRecordModelKeys()
        index = 0
        results = []
        sub_order_list = tradeDetailJson['sub_order_list']
        for sub_order in sub_order_list:
            for order in sub_order['orders']:
                opType = order['action_desc']
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
                    if opType == '买入' or opType == '转换':
                        occurMoney = round(confirm_amount + fee, 2)
                    elif opType == '卖出':
                        occurMoney = round(confirm_amount - fee, 2)
                    else:
                        continue
                all_model_values.append(nav_acc)
                all_model_values.append(confirm_volume)
                all_model_values.append(confirm_amount)
                all_model_values.append(fee)
                all_model_values.append(occurMoney)
                all_model_values.append(self.owner + '_' + global_name + '_' + order['plan_name'])
                categoryInfo = self.categoryManager.getCategoryByCode(all_model_values[2])
                if categoryInfo != {}:
                    all_model_values.append(categoryInfo['category1'])
                    all_model_values.append(categoryInfo['category2'])
                    all_model_values.append(categoryInfo['category3'])
                    all_model_values.append(categoryInfo['categoryId'])
                all_model_values.append('https://danjuanapp.com/djmodule/trade-details?ordertype=plan&orderid=' + order['order_id'])
                itemDict = dict(zip(all_model_keys, all_model_values))
                results.append(itemDict)
        return results

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