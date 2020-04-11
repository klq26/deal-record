# -*- coding: utf-8 -*-

import os
import sys
import json
import math
from datetime import datetime
from datetime import timedelta
import ssl

from urllib import parse
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

import pandas as pd

from login.requestHeaderManager import requestHeaderManager
from category.categoryManager import categoryManager
from database.fundDBHelper import fundDBHelper
from spider.common.dealRecordModel import *

global_name = '天天'

class tiantianSpider:

    def __init__(self, strategy = 'klq'):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.categoryManager = categoryManager()
        if strategy == 'klq':
            self.owner = '康力泉'
            self.headers = requestHeaderManager().getTiantianKLQ()
            self.dateIntervals = self.getDateIntervals()
        elif strategy == 'lsy':
            self.owner = '李淑云'
            self.headers = requestHeaderManager().getTiantianLSY()
            self.dateIntervals = self.getDateIntervals(startYear = 2018, startMonth = 1, startDay = 1)
        # 交易详情 url 数组（后续逐个解析）
        self.detailUrlList = []
        self.results = []
        self.tradelists = []
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
        print('天天：{0} 获取中..'.format(self.owner))
        # 准备成交记录列表
        tradelistJson = self._prepareTradelist(forceUpdate = forceUpdate)
        for tradeRecord in tradelistJson:
            [self.detailUrlList.append(x) for x in self.getDetailUrlsFromTradeList(tradeRecord['html'])]
        # print(len(self.detailUrlList))
        # 获取每一条详情数据
        dealRecordJsonList = self._prepareDetailList(self.detailUrlList)
        index = 0
        for i in range(0, len(dealRecordJsonList)):
            x = dealRecordJsonList[i]
            item = self._prepareDealRecords(x, index + 1)
            if item != None:
                index += 1
                self.results.append(item)
        # 写入文件
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(self.results, ensure_ascii = False, indent = 4))
        return self.results

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
            df.to_csv(os.path.join(self.folder, 'output', '{0}-tiantian-unique-codes.csv'.format(self.owner)), sep='\t')
            return df
            # df.to_excel('code-name.xlsx')

    def load(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    # 根据今天日期和起始日期,生成多个 90 天时间间隔的二维数组
    def getDateIntervals(self, startYear = 2016, startMonth = 5, startDay = 1, interval = 90):
        dateIntervals = []
        # 起始日期为开户日
        startDate = datetime(year = startYear, month = startMonth, day = startDay)
        # 间隔 90 天
        interval_days = timedelta(days = interval)
        # 和起始日间隔 90 天后的日期
        endDate = startDate + interval_days
        # 终止日期为今天
        today = datetime.now()
        # 字符串格式化
        fmt = '%Y-%m-%d'
        while max(today, endDate) == today:
            # print(startDate.strftime(fmt), endDate.strftime(fmt))
            dateIntervals.append({'startDate': startDate.strftime(fmt), 'endDate': endDate.strftime(fmt), 'duration': interval_days.days})
            startDate = endDate + timedelta(days=1)
            endDate = startDate + interval_days
        # 最后一条不足 90 天的数据
        startDate = endDate - interval_days
        endDate = today
        # print(startDate.strftime(fmt), endDate.strftime(fmt))
        dateIntervals.append({'startDate': startDate.strftime(fmt), 'endDate': endDate.strftime(fmt), 'duration': (today - startDate).days})
        return dateIntervals

    # 整合所有的交易列表，生成详情 url 集合
    def getDetailUrlsFromTradeList(self, htmlText):
        detail_url_list = []
        detail_url_prefix = u'https://query.1234567.com.cn'
        soup = BeautifulSoup(htmlText, 'lxml')
        results = soup.findAll(lambda e: e.name == 'a' and '详情' in e.text)
        # 接口拿回来默认是时间倒叙的
        results = list(reversed(results))
        [detail_url_list.append(detail_url_prefix + x['href']) for x in results]
        return detail_url_list

    # 获取详细交易数据的整合信息
    def getDetailInfo(self, htmlText, url):
        soup = BeautifulSoup(htmlText, 'lxml')
        results = soup.findAll('div',{'class':'ui-confirm'})
        
        applyInfo_keys = ['applyDate','applyOperate','applyStatus']
        confirmInfo_keys = ['fundName', 'fundCode', 'confirmDate', 'confirmOperate', 'confirmStatus', 'confirmNavUnit', 'confirmNavAcc', 'confirmMoney', 'confirmVolume', 'fee']
        
        jsonData = {'申请信息': {}, '确认信息': {}, '详情页': url }
        # 申请日期（拿累计净值）
        applyDate = ''
        for x in results:
            h3_array = x.select('h3')
            # 结果
            values = []
            if len(h3_array) > 0 and h3_array[0].text == u'申请信息':
                if len(x.select('table')) > 0:
                    # 所有值
                    tags = x.select('table')[0].tbody.findAll('td')
                    # 不要“申请数额”
                    tags.pop(-2)
                    # 不要“标题<br/>代码”
                    tags.pop(1)
                    [values.append(x.text) for x in tags]
                    jsonData['申请信息'] = (dict(zip(applyInfo_keys, values)))
                    applyDate = jsonData['申请信息']['applyDate']
            if len(h3_array) > 0 and h3_array[0].text == u'确认信息':
                if len(x.select('table')) > 0:
                    # 所有值
                    tags = x.select('table')[0].tbody.findAll('td')
                    # “标题<br/>代码”
                    a = tags.pop(1).a
                    # 标题
                    values.append(a.contents[0])
                    # 代码
                    values.append(a.contents[2])
                    [values.append(x.text) for x in tags]
                    # 拿一下累计净值
                    values.insert(6, '待实现')
                    jsonData['确认信息'] = (dict(zip(confirmInfo_keys, values)))
        return jsonData

    ########################################################################
    # private methods
    ########################################################################

    # 准备交易列表 json 数据
    def _prepareTradelist(self, forceUpdate = False):
        results = []
        deal_list_url = u'https://query.1234567.com.cn/Query/DelegateList?DataType=1&StartDate={0}&EndDate={1}&BusType=0&Statu=0&Account=&FundType=0&PageSize=500&PageIndex=1'
        # 获取所有的成交记录概述
        if forceUpdate:
            for interval in self.dateIntervals:
                response = requests.get(deal_list_url.format(interval['startDate'], interval['endDate']), headers=self.headers, verify=False)
                if response.status_code == 200 and u'class=' in response.text:
                    interval['html'] = response.text
                    results.append(interval)
                else:
                    print('[ERROR] tiantianSpider tradelist.json 获取失败 code:{0} text:{1}'.format(response.status_code, response.text))
                    exit(1)
            # 写入
            with open(self.tradelist_file, 'w+', encoding='utf-8') as f:
                f.write(json.dumps(results, ensure_ascii=False, indent = 4))
            return results
        else:
            if os.path.exists(self.tradelist_file):
                with open(self.tradelist_file, 'r', encoding='utf-8') as f:
                    results = json.loads(f.read())
                    return results
            else:
                # 没有缓存的话，无论如何也得去下载
                for interval in self.dateIntervals:
                    response = requests.get(deal_list_url.format(interval['startDate'], interval['endDate']), headers=self.headers, verify=False)
                    if response.status_code == 200 and u'class=' in response.text:
                        interval['html'] = response.text
                        results.append(interval)
                    else:
                        print('[ERROR] tiantianSpider tradelist.json 获取失败 code:{0} text:{1}'.format(response.status_code, response.text))
                        exit(1)
                    # 写入
                    with open(self.tradelist_file, 'r', encoding='utf-8') as f:
                        f.write(json.dumps(results, ensure_ascii=False, indent = 4))
                    return results

    # 根据 tradelist.json 中的数组，准备每一条交易详情数据
    def _prepareDetailList(self, detailUrlList, forceUpdate = False):
        htmlText = ''
        orderJsonList = []
        detailinfo_path = os.path.join(self.detailfolder, 'detail.json')
        # 强制更新会覆盖最后一条不足 90 天时间间隔的数据，间接实现了增量更新。
        if forceUpdate:
            length = len(detailUrlList)
            # length = 15
            for i in range(0, length):
                detailUrl = detailUrlList[i]
                response = requests.get(detailUrl, headers = self.headers, verify=False)
                if response.status_code == 200 and u'class=' in response.text:
                    htmlText = response.text
                    jsonData = self.getDetailInfo(htmlText, detailUrl)
                    orderJsonList.append(jsonData)
                    print('\r{0}%'.format(round(i / length * 100, 2)), end='', flush=True)
                else:
                    print('[ERROR] tiantianSpider detail.json 获取失败 code:{0} text:{1}'.format(response.status_code, response.text))
                    exit(1)
            # 写入 detail.json
            with open(detailinfo_path, 'w+', encoding='utf-8') as f:
                f.write(json.dumps(orderJsonList, ensure_ascii = False, indent = 4))
            return orderJsonList
        else:
            if os.path.exists(detailinfo_path):
                with open(detailinfo_path, 'r', encoding='utf-8') as f:
                    orderJsonList = json.loads(f.read())
                    return orderJsonList
            else:
                # 没有缓存的话，无论如何也得去下载
                length = len(detailUrlList)
                # length = 15
                for i in range(0, length):
                    detailUrl = detailUrlList[i]
                    response = requests.get(detailUrl, headers = self.headers, verify=False)
                    if response.status_code == 200 and u'class=' in response.text:
                        htmlText = response.text
                        jsonData = self.getDetailInfo(htmlText, detailUrl)
                        orderJsonList.append(jsonData)
                        print('\r{0}%'.format(round(i / length * 100, 2)), end='', flush=True)
                    else:
                        print('[ERROR] tiantianSpider detail.json 获取失败 code:{0} text:{1}'.format(response.status_code, response.text))
                        exit(1)
                # 写入 detail.json
                with open(detailinfo_path, 'w+', encoding='utf-8') as f:
                    f.write(json.dumps(orderJsonList, ensure_ascii = False, indent = 4))
            return orderJsonList

    # 根据 trade detail.json 中的数组，准备每一条成交记录
    def _prepareDealRecords(self, x, index):
        db = fundDBHelper()
        # 输出 record
        all_model_keys = dealRecordModelKeys()
        # 这是2020年3月31日从历史记录中提取的所有可能的操作名称，如果不在这个之中，应该中断程序，查看原因，升级代码，防止录入错误的交易记录。
        # 快速过户 = 快速取现金到银行卡，忽略
        # 转出投资账户确认 & 转入投资账户确认，忽略
        # 红利发放，只需要指数基金的
        # 强行调增，即拆分信息
        # 申购确认，赎回确认，都要
        allOpType = ['申购确认', '赎回确认', '红利发放(红利再投资)', '红利发放(现金分红)', '快速过户', '转出投资账户确认', '转入投资账户确认','强行调增', '强行调减']
        allNeededType = ['申购确认', '赎回确认', '红利发放(红利再投资)', '红利发放(现金分红)', '强行调增', '强行调减']
        # 取关键信息
        applyInfo = x['申请信息']
        hasApply = applyInfo != {}
        confirmInfo = x['确认信息']
        hasConfirm = confirmInfo != {}
        # 过滤
        if not hasConfirm:
            opInfo = '未知'
            if hasApply:
                opInfo = applyInfo['applyStatus']
            print('[Warning] tiantianSpider 忽略非正常交易详情：{0}\n{1}\n'.format(opInfo, x))
            return None
        opType = confirmInfo['confirmOperate']
        if opType not in allOpType:
            print('[ERROR] tiantianSpider 未知操作类型：{0}'.format(opType))
            exit(1)
        # 不要货币基金
        if u'货币' in confirmInfo['fundName']:
            print('[Warning] tiantianSpider 忽略货币基金交易详情：{0}\n{1}\n'.format(opType, x))
            return None
        # 开始录入成交数据
        all_model_values = []
        all_model_values.append(index)
        fee = confirmInfo['fee']
        confirmMoney = confirmInfo['confirmMoney']
        volume = confirmInfo['confirmVolume']
        dealMoney = 0
        occurMoney = 0
        nav_unit = round(float(confirmInfo['confirmNavUnit']), 4)
        nav_acc = 0.0
        if u'红利发放' in opType:
            # 分红的意思就是，被动操作，没有 applyInfo
            all_model_values.append(confirmInfo['confirmDate'])
            all_model_values.append(confirmInfo['fundCode'])
            all_model_values.append(confirmInfo['fundName'])
            all_model_values.append('分红')
            occurMoney = confirmMoney
            db_record = db.selectNearestDividendDateFundNav(code = all_model_values[2], date = all_model_values[1])
            if nav_unit == 0.0:
                nav_unit = db_record[1]
            nav_acc = db_record[2]
        elif u'强行调增' in opType:
            # 强行调增的意思就是，被动操作，没有 applyInfo
            all_model_values.append(confirmInfo['confirmDate'])
            all_model_values.append(confirmInfo['fundCode'])
            all_model_values.append(confirmInfo['fundName'])
            all_model_values.append('分红')
            occurMoney = confirmMoney
            db_record = db.selectNearestSplitDateFundNav(code = all_model_values[2], date = all_model_values[1])
            if nav_unit == 0.0:
                nav_unit = db_record[1]
            nav_acc = db_record[2]
        else:
            all_model_values.append(applyInfo['applyDate'])
            all_model_values.append(confirmInfo['fundCode'])
            all_model_values.append(confirmInfo['fundName'])
            if '申' in opType:
                all_model_values.append('买入')
                occurMoney = confirmMoney
                dealMoney = round(float(occurMoney) - float(fee), 2)
            elif '赎' in opType:
                all_model_values.append('卖出')
                dealMoney = confirmMoney
                occurMoney = round(float(dealMoney) - float(fee), 2)
            else:
                # 目前只处理指数基金的买入，卖出，分红
                print('[Warning] tiantianSpider 忽略买、卖、及分红以外的交易：{0}\n{1}\n'.format(opType, x))
                all_model_values.append('错误')
                return None
            nav_acc = db.selectFundNavByDate(code = all_model_values[2], date = all_model_values[1])[2]
        all_model_values.append(nav_unit)
        # 如果查询的是货币基金，没有库存时返回 -1
        if nav_acc == -1:
            all_model_values.append(nav_unit)
        # 如果库存单位净值和网站给出精确一致，则应用库存累计净值
        all_model_values.append(round(float(nav_acc), 4))
        all_model_values.append(round(float(volume), 2))
        all_model_values.append(round(float(dealMoney), 2))
        all_model_values.append(round(float(fee), 2))
        all_model_values.append(round(float(occurMoney), 2))
        all_model_values.append(self.owner + '_' + global_name)
        categoryInfo = self.categoryManager.getCategoryByCode(all_model_values[2])
        if categoryInfo != {}:
            all_model_values.append(categoryInfo['category1'])
            all_model_values.append(categoryInfo['category2'])
            all_model_values.append(categoryInfo['category3'])
            all_model_values.append(categoryInfo['categoryId'])
        all_model_values.append(x['详情页'])
        itemDict = dict(zip(all_model_keys, all_model_values))
        # DEBUG
        # [print(x) for x in allOpType]
        # [print(x) for x in allMoneyFundFenHong]
        return itemDict

if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'lsy\'：李淑云')
        exit()
    # 传入配置，开始流程
    spider = tiantianSpider(strategy = strategy)
    spider.get()