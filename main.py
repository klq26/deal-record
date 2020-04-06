import os
import sys
import json

import pandas as pd
from pandas.io.json import json_normalize

from login.account import account
from login.requestHeaderManager import requestHeaderManager
from tools.fundInfoSpider import fundInfoSpider
from tools.fundNavUpdater import fundNavUpdater
from tools.dividendInfoSpider import dividendInfoSpider
from database.fundDBHelper import fundDBHelper
from database.dealRecordDBHelper import dealRecordDBHelper
from category.categoryManager import categoryManager
from analytics.accountAnalytics import accountAnalytics
from spider.tiantian.tiantianSpider import tiantianSpider
from spider.danjuan.danjuanSpider import danjuanSpider
from spider.qieman.qiemanSpider import qiemanSpider
from spider.zhifubao.zhifubaoSpider import zhifubaoSpider
from spider.huatai.huataiSpider import huataiSpider
from spider.huabao.huabaoSpider import huabaoSpider

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

# 获取康力泉所有非货币基金的交易记录
def getKLQ():
    return [tiantianSpider(), danjuanSpider(), qiemanSpider(), zhifubaoSpider(), huataiSpider(), huabaoSpider()]

# 获取父母所有非货币基金的交易记录
def getParent():
    return [tiantianSpider('lsy'), danjuanSpider('lsy'), danjuanSpider('ksh'), qiemanSpider('ksh')]

# 获取所有交易记录
def allUniqueCodes(strategy = 'klq'):
    df = pd.DataFrame()
    spiders = []
    [spiders.append(x) for x in getKLQ()]
    [spiders.append(x) for x in getParent()]
    for account in spiders:
        print(account)
        df = df.append(account.uniqueCodes())
    return categoryManager().allUniqueCodes(df)

def allDealRecords(strategy = 'klq'):
    folder = os.path.abspath(os.path.dirname(__file__))
    output_path = os.path.join(folder, u'{0}_allDealRecords.xlsx'.format(strategy))
    records = []
    if strategy == 'klq':
        spiders = getKLQ()
    else:
        spiders = getParent()
    for account in spiders:
        print(account)
        [records.append(x) for x in account.load()]
    # 日期升序，重置 id
    records.sort(key=lambda x: x['date'])
    for i in range(1, len(records) + 1):
        records[i-1]['id'] = i
    # [print(x) for x in records]
    df = json_normalize(records)
    columns = ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', 'note']
    df = df.reindex(columns = columns)
    record_db = dealRecordDBHelper()
    for item in df.values:
        record_db.insertDataToTable(tablename=strategy, keys=columns, values = item)
    df.to_excel(output_path)

# 显示库中不认识的基金代码及名称
def showCategoryUnknownFunds(strategy = 'klq'):
    folder = os.path.abspath(os.path.dirname(__file__))
    category_df = pd.read_excel(os.path.join(folder, u'category', u'资产配置分类表.xlsx'))
    category_df['基金代码'] = [str(x).zfill(6) for x in category_df['基金代码'].values]
    # 基金代码库
    category_codes = list(category_df['基金代码'])
    target_df = allUniqueCodes(strategy)
    for i in range(0,len(target_df.code.values)):
        code = target_df.code.values[i]
        name = target_df.name.values[i]
        if code not in category_codes:
            print(code, name)

# 更新新的基金信息到数据库（包括基本信息，历史单位，累计净值等）
def insertNewFundInfos():
    db = fundDBHelper()
    folder = os.path.abspath(os.path.dirname(__file__))
    fund_data_folder = os.path.join(folder, 'tools','fund_data')
    for root, dirs, files in os.walk(fund_data_folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            code = filename.split('_')[0]
            with open(filepath, 'r',encoding='utf-8') as f:
                db.insertFundByJonsData(json.loads(f.read()))

# 更新数据库
def updateDatabase():
    # 更新数据库中的净值到今天
    updater = fundNavUpdater()
    updater.update()
    # 拉取库存基金的历史分红信息
    # divide = dividendInfoSpider()
    # divide.get(db.selectAllFundNavCodes())
    # TODO 这里的 get 同样要先监测库里该基金的最新一条分红数据
    # divide.insertToDB()

if __name__ == "__main__":
    # cls()
    # 更新数据库
    # updateDatabase()
    # 插入全部记录
    # allDealRecords('klq')
    # allDealRecords('parents')
    # 康力泉
    # accountAnalytics().getAccount('华泰')
    # accountAnalytics().getAccount('华宝')
    # accountAnalytics().getAccount('天天')
    # accountAnalytics().getAccount('150份')
    # accountAnalytics().getAccount('S定投')
    # accountAnalytics().getAccount('螺丝钉')
    # accountAnalytics().getAccount('钉钉宝365')
    # accountAnalytics().getAccount('支付宝')
    accountAnalytics().getAccount('钉钉宝90天')
    # 父母
    # accountAnalytics('lsy').getAccount('天天')
    # accountAnalytics('lsy').getAccount('李淑云_蛋卷_钉钉宝365天组合')
    # accountAnalytics('lsy').getAccount('康世海_蛋卷_钉钉宝365天组合')
    # accountAnalytics('ksh').getAccount('且慢')
    accountAnalytics('lsy').getAccount('李淑云_蛋卷_钉钉宝90天组合')
    accountAnalytics('ksh').getAccount('康世海_蛋卷_钉钉宝90天组合')