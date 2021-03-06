# -*- coding: utf-8 -*-

# local bin
import os
import sys
import json
from datetime import datetime
# third partys
import pandas as pd
from pandas.io.json import json_normalize
# login
from login.account import account
from login.requestHeaderManager import requestHeaderManager
# tools
from tools.fundInfoSpider import fundInfoSpider
from tools.dividendInfoSpider import dividendInfoSpider
from tools.fundNavUpdater import fundNavUpdater
# database
from database.fundDBHelper import fundDBHelper
from database.dealRecordDBHelper import *
# model
from spider.common.dealRecordModel import *
# category
from category.categoryManager import categoryManager
# analytics
from analytics.accountAnalytics import accountAnalytics
from analytics.analyticsManager import analyticsManager
# spiders
from spider.tiantian.tiantianSpider import tiantianSpider
from spider.danjuan.danjuanSpider import danjuanSpider
from spider.qieman.qiemanSpider import qiemanSpider
from spider.zhifubao.zhifubaoSpider import zhifubaoSpider
from spider.huatai.huataiSpider import huataiSpider
from spider.huabao.huabaoSpider import huabaoSpider

from app.server.evalManager import evalManager

# https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.set_option.html
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
# 不折行显示列
pd.set_option('expand_frame_repr', False)
# 默认 50
pd.set_option('max_colwidth',40)

def temp():
    # tiantian_moneyFundCode = ['000588', '000600', '000638', '000709', '000891', '001666', '002183', '003003', '003022', '003474', '005148', '340005']
    # tiantian_lsy_moneyFundCode = ['000509', '000600', '000638', '000891', '003474', '360003', '482002']
    pass

# 清屏
def cls():
    if sys.platform.startswith('win'):
        os.system('cls')
    elif sys.platform.startswith('linux'):
        os.system('clear')

# 获取康力泉所有非货币基金的交易的 json 原始记录
def getKLQSpiders():
    return [tiantianSpider(), danjuanSpider(), qiemanSpider(), zhifubaoSpider(), huataiSpider(), huabaoSpider()]

# 获取父母所有非货币基金的交易记录的 json 原始记录
def getParentsSpiders():
    return [tiantianSpider('lsy'), danjuanSpider('lsy'), danjuanSpider('ksh'), qiemanSpider('ksh')]

# 获取所有交易记录
def allUniqueCodes(strategy = ''):
    df = pd.DataFrame()
    spiders = []
    if strategy == '':
        [spiders.append(x) for x in getKLQSpiders()]
        [spiders.append(x) for x in getParentsSpiders()]
    elif strategy == 'klq':
        [spiders.append(x) for x in getKLQSpiders()]
    elif strategy == 'parents':
        [spiders.append(x) for x in getParentsSpiders()]
    else:
        print('[ERROR] 错误的 strategy：{0}'.format(strategy))
        exit(1)
    for account in spiders:
        df = df.append(account.uniqueCodes())
    df = df.drop_duplicates(['code'])
    df = df.sort_values(by='code' , ascending=True)
    df = df.reset_index(drop=True)

# 输出所有成交记录（本地是 {0}_updateAllDealRecords.csv，云端是 mysql 数据库）
def updateAllDealRecords(strategy = 'klq', onlyUpdatelocal = True):
    folder = os.path.abspath(os.path.dirname(__file__))
    output_path = os.path.join(folder, u'{0}_updateAllDealRecords.csv'.format(strategy))
    records = []
    if strategy == 'klq':
        spiders = getKLQSpiders()
    else:
        spiders = getParentsSpiders()
    for account in spiders:
        [records.append(x) for x in account.load()]
    # 日期升序，重置 id
    records.sort(key=lambda x: x['date'])
    for i in range(1, len(records) + 1):
        records[i-1]['id'] = i
    # [print(x) for x in records]
    df = json_normalize(records)
    columns = dealRecordModelKeys()
    df = df.reindex(columns = columns)
    record_db = dealRecordDBHelper()
    # 取数据库最新一条
    sql = u"SELECT * FROM {0} ORDER BY id DESC LIMIT 1".format(strategy)
    latest = record_db.selectByCommand(sql)
    latestId = 0
    if len(latest) > 0:
        latestId = latest.id.values[0]
    for item in df.values:
        if not onlyUpdatelocal:
            recordId = item[0]
            # 忽略已经入库的记录
            if recordId <= latestId:
                # print('忽略 {0}'.format(recordId))
                continue
            record_db.insertDataToTable(tablename=strategy, keys=columns, values = item)
    df.to_csv(output_path)

# 把家庭当前的持仓记录，历史清仓数据写入数据库
def allFamilyHoldingSelloutStatus(onlyUpdatelocal = True):
    # 获取整体情况
    holding_df, sellout_df = analyticsManager().getFamilyHoldingSelloutStatus()
    # holding
    holding_df['id'] = [x for x in range(1, len(holding_df) + 1)]
    # 给定 Column 排序
    holding_df = holding_df[familyHoldingDBKeys()]
    if not onlyUpdatelocal:
        db = dealRecordDBHelper()
        db.truncateTable('family_holding')
        db.insertFamilyHoldingByDataFrame(holding_df)
    # sell out
    sellout_df['id'] = [x for x in range(1, len(sellout_df) + 1)]
    # 给定 Column 排序
    sellout_df = sellout_df[familyHoldingDBKeys()]
    if not onlyUpdatelocal:
        db = dealRecordDBHelper()
        db.truncateTable('family_sellout')
        db.insertFamilySelloutByDataFrame(sellout_df)

# 把每只基金当前的持仓记录数据写入数据库
def allFundHoldingStatus(onlyUpdatelocal = True):
    holding_df = analyticsManager().getFundHoldingStatus()
    holding_df['id'] = [x for x in range(1, len(holding_df) + 1)]
    # print(holding_df)
    holding_df['account'] = u'不适用'
    if not onlyUpdatelocal:
        db = dealRecordDBHelper()
        db.truncateTable('fund_holding')
        db.insertFundHoldingByDataFrame(holding_df)

# 显示库中不认识的基金代码及名称
def showCategoryUnknownFunds(strategy = 'klq'):
    category_df = categoryManager().getCategoryDataFrame()
    # 基金代码库
    category_codes = list(category_df['基金代码'])
    target_df = allUniqueCodes(strategy)
    for i in range(0,len(target_df.code.values)):
        code = target_df.code.values[i]
        name = target_df.name.values[i]
        if code not in category_codes:
            print(code, name)

# 更新新的基金信息到数据库（包括基本信息，历史单位，累计净值等）
def insertNewFundInfosToDB():
    db = fundDBHelper()
    folder = os.path.abspath(os.path.dirname(__file__))
    fund_data_folder = os.path.join(folder, 'tools','fund_data')
    for root, dirs, files in os.walk(fund_data_folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            with open(filepath, 'r',encoding='utf-8') as f:
                # 用 dbHelper 的 json adapter 直接插入整个基金基础数据
                db.insertFundByJonsData(json.loads(f.read()))

# 更新数据库
def updateDatabase():
    folder = os.path.abspath(os.path.dirname(__file__))
    today = datetime.now().strftime('%Y-%m-%d')
    with open(os.path.join(folder, 'navUpdateTime.json'), 'r',encoding='utf-8') as f:
        config = json.loads(f.read())
        if today == config['date']:
            # print('净值库已更新，退出')
            return
    # 更新数据库中的净值到今天
    updater = fundNavUpdater()
    updater.update()
    # 拉取库存基金的历史分红信息
    divide = dividendInfoSpider()
    # 清理数据库基金分红拆分数据
    divide.truncateDB()
    # 获取最新
    db = fundDBHelper()
    codes = db.selectAllFundNavCodes()
    divide.get(codes)
    # TODO 这里的 get 同样要先监测库里该基金的最新一条分红数据
    # 插入数据库
    divide.insertToDB(codes)
    with open(os.path.join(folder, 'navUpdateTime.json'), 'w+',encoding='utf-8') as f:
        f.write(json.dumps({'date':today}, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    # 更新数据库
    # updateDatabase()

    # 所有spider increment
    # qiemanSpider('klq').get(True)
    # tiantianSpider('klq').get(True)
    # tiantianSpider('lsy').get(True)
    # huabaoSpider().get()
    # huataiSpider().get()
    # danjuanSpider('klq').increment()
    # danjuanSpider('lsy').increment()
    # danjuanSpider('ksh').increment()
    # danjuanSpider('ksh').get(True)
    # danjuanSpider('klq').get(True)
    # danjuanSpider('lsy').get(True)

    # # 插入增量数据或全量数据
    updateAllDealRecords('klq', onlyUpdatelocal = False)
    updateAllDealRecords('parents', onlyUpdatelocal = False)

    # # 更新汇总持仓数据到数据库（供 familyHolding app 使用）
    allFamilyHoldingSelloutStatus(onlyUpdatelocal = False)
    allFundHoldingStatus(onlyUpdatelocal = False)