import os
import sys
import json

from login.account import account
from login.requestHeaderManager import requestHeaderManager
from tools.fundInfoSpider import fundInfoSpider
from tools.fundNavUpdater import fundNavUpdater
from database.fundDBHelper import fundDBHelper
from spider.tiantian.tiantianSpider import tiantianSpider
from spider.danjuan.danjuanSpider import danjuanSpider
from spider.qieman.qiemanSpider import qiemanSpider
from spider.huatai.huataiSpider import huataiSpider
from spider.huatai.huataiHistory import huataiHistory
from spider.huabao.huabaoSpider import huabaoSpider

if __name__ == "__main__":
    # 清屏
    if sys.platform.startswith('win'):
        os.system('cls')
    elif sys.platform.startswith('linux'):
        os.system('clear')
    
    # 测试系统路径
    # [print(x) for x in sys.path]

    tiantian = tiantianSpider(strategy='klq')
    # tiantian.get()
    # df = tiantian.uniqueCodes()
    # tiantian_allCode = list(df['code'])
    # print(df)
    # tiantian_indexFundCode = ['000071', '000179', '000478', '000614', '000968', '001061', '001064', '001180', '001469', '002903', '003376', '003647', '004752', '050025', '100032', '100038', '110022', '110026', '110027', '161017', '161725', '162411', '164906', '340001', '501018', '519977']
    # tiantian_moneyFundCode = ['000588', '000600', '000638', '000709', '000891', '001666', '002183', '003003', '003022', '003474', '005148', '340005']
    # tiantian_lsy_indexFundCode = ['000051', '000071', '000216', '000478', '000614', '000968', '001051', '001064', '001112', '001180', '001469', '002903', '003765', '004752', '050025', '100032', '100038', '110022', '110026', '110027', '161017', '162411', '162413', '162711', '164906', '340001', '501018', '502010', '519977']
    # tiantian_lsy_moneyFundCode = ['000509', '000600', '000638', '000891', '003474', '360003', '482002']
    # 下载天天基金历史净值
    # fundInfoSpider().get(['000051', '001112', '162413', '162711'])

    danjuan = danjuanSpider(strategy='klq')
    danjuan.get()
    # df = danjuan.uniqueCodes()
    # print(df)
    # danjuan_allCode = list(df['code'])
    # print(danjuan_allCode)
    danjuan_indexFunCode = ['001338', '001550', '001594', '002086', '002147', '003318', '006060', '006320', '006327', '007749', '040046', '070023', '090010', '161128', '310398', '485011', '501021', '501029', '501050', '519153', '519671', '530015']
    # for code in danjuan_indexFunCode:
    #     if code not in tiantian_indexFundCode:
    #         print(code)
    # 下载蛋卷基金历史净值（已从天天基金中去重）
    # fundInfoSpider().get(danjuan_indexFunCode)

    qieman = qiemanSpider(strategy='ksh')
    # qieman.get()
    # df = qieman.uniqueCodes()
    # qieman_allCode = list(df['code'])
    # print(df)
    # print(qieman_allCode)
    # 下载且慢基金历史净值（已从天天基金，蛋卷基金中去重）
    qieman_indexFunCode = ['000216', '001051', '001052', '003765', '160416', '502010']
    # for code in qieman_indexFunCode:
    #     if code not in tiantian_indexFundCode and code not in danjuan_indexFunCode:
    #         print(code)
    # fundInfoSpider().get(['006793', '164902', '519700', '519718', '519723', '519738', '519752', '519755', '519776'])

    # huatai = huataiSpider()
    # huatai.get()

    # huabao = huabaoSpider()
    # huabao.get()

    # 写入数据库
    db = fundDBHelper()
    # print(db.selectFundNavByDate('100032','2018-01-19'))
    # db_tables = db.getAllCodesInDB()
    # for code in db_tables:
    #     results = db.selectLatestRecordFromTable(code)
    #     print(code, results)

    # 创建 fund_info 数据库
    # db.addFundInfoTableIfNeeded()
    # folder = os.path.join(os.getcwd(), 'tools','fund_data')
    # for root, dirs, files in os.walk(folder):
    #     for filename in files:
    #         filepath = os.path.join(root, filename)
    #         code = filename.split('_')[0]
    #         with open(filepath, 'r',encoding='utf-8') as f:
    #             db.insertFundByJonsData(json.loads(f.read()))

    # 拉最新数据
    # for item in tiantian_indexFundCode:
    #     results = db.selectLatestRecordFromTable(item)
    #     print(item, results)
    # for item in danjuan_indexFunCode:
    #     results = db.selectLatestRecordFromTable(item)
    #     print(item, results)
    # for item in qieman_indexFunCode:
    #     results = db.selectLatestRecordFromTable(item)
    #     print(item, results)

    # 更新数据库中的净值到今天
    # updater = fundNavUpdater()
    # updater.update()
