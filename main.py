import os
import sys
import json

from login.account import account
from login.requestHeaderManager import requestHeaderManager
from tools.fundInfoSpider import fundInfoSpider
from database.fundDBHelper import fundDBHelper
from spider.tiantian.tiantianSpider import tiantianSpider
from spider.danjuan.danjuanSpider import danjuanSpider
from spider.qieman.qiemanSpider import qiemanSpider

if __name__ == "__main__":
    # 测试系统路径
    # [print(x) for x in sys.path]

    tiantian = tiantianSpider()
    tiantian.get()
    # df = tiantian.uniqueCodes()
    # tiantian_allCode = list(df['code'])
    tiantian_indexFundCode = ['000071', '000179', '000478', '000614', '000968', '001061', '001064', '001180', '001469', '002903', '003376', '003647', '004752', '050025', '100032', '100038', '110022', '110026', '110027', '161017', '161725', '162411', '164906', '340001', '501018', '519977']
    # tiantian_moneyFundCode = ['000588', '000600', '000638', '000709', '000891', '001666', '002183', '003003', '003022', '003474', '005148', '340005']
    # 下载天天基金历史净值
    # fundInfoSpider().get(tiantian_indexFundCode)

    danjuan = danjuanSpider()
    # danjuan.get()
    # df = danjuan.uniqueCodes()
    # danjuan_allCode = list(df['code'])
    danjuan_indexFunCode = ['001338', '001550', '001594', '002086', '002147', '003318', '006060', '006320', '006327', '007749', '040046', '070023', '090010', '161128', '310398', '485011', '501021', '501029', '501050', '519153', '519671', '530015']
    # for code in danjuan_indexFunCode:
    #     if code not in tiantian_indexFundCode:
    #         print(code)
    # 下载蛋卷基金历史净值（已从天天基金中去重）
    # fundInfoSpider().get(danjuan_indexFunCode)

    qieman = qiemanSpider()
    # qieman.get()
    # df = qieman.uniqueCodes()
    # qieman_allCode = list(df['code'])
    # 下载且慢基金历史净值（已从天天基金，蛋卷基金中去重）
    qieman_indexFunCode = ['000216', '001051', '001052', '003765', '160416', '502010']
    # for code in qieman_indexFunCode:
    #     if code not in tiantian_indexFundCode and code not in danjuan_indexFunCode:
    #         print(code)
    # fundInfoSpider().get(qieman_indexFunCode)

    # 写入数据库
    db = fundDBHelper()
    # print(db.getAllCodesInDB())
    # # 创建 fund_info 数据库
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
