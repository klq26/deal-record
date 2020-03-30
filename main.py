import os
import sys
import json

from login.account import account
from login.requestHeaderManager import requestHeaderManager
from spider.tiantian.tiantianSpider import tiantianSpider
from tools.fundInfoSpider import fundInfoSpider
from database.fundDBHelper import fundDBHelper

if __name__ == "__main__":
    # 测试系统路径
    # [print(x) for x in sys.path]

    # tiantianSpider().get()
    # 获取所有记录中的唯一代码
    # with open(os.path.join(os.getcwd(), 'spider', 'tiantian','output','康力泉_record.json'), 'r', encoding='utf-8') as f:
    #     import json
    #     datalist = json.loads(f.read())
    #     names = []
    #     codes = []
    #     for x in datalist:
    #         if 'fundName' in x['确认信息'].keys():
    #             names.append(x['确认信息']['fundName'])
    #         if 'fundCode' in x['确认信息'].keys():
    #             codes.append(x['确认信息']['fundCode'])
    #     import pandas as pd
    #     df = pd.DataFrame()
    #     df['name'] = names
    #     df['code'] = codes
    #     df = df.drop_duplicates(['code'])
    #     df.to_excel('code-name.xlsx')
    
    tiantian_indexFundCode = ['000071', '000179', '000478', '000614', '000968', '001061', '001064', '001180', '001469', '002903', '003376', '003647', '004752', '050025', '100032', '100038', '110022', '110026', '110027', '161017', '161725', '162411', '164906', '340001', '501018', '519977']
    # tiantian_moneyFundCode = ['000588', '000600', '000638', '000709', '000891', '001666', '002183', '003003', '003022', '003474', '005148', '340005']

    # 下载基金历史净值
    # fundInfoSpider().get(['000071', '000179', '000478', '000614', '000968', '001061', '001064', '001180', '001469', '002903', '003376', '003647', '004752', '050025', '100038', '110022', '110026', '110027', '161017', '161725', '162411', '164906', '340001', '501018', '519977'])

    # 写入数据库
    db = fundDBHelper()
    # 创建 fund_info 数据库
    db.addFundInfoTableIfNeeded()
    folder = os.path.join(os.getcwd(), 'tools','fund_data')
    for root, dirs, files in os.walk(folder):
        for filename in files:
            filepath = os.path.join(root, filename)
            code = filename.split('_')[0]
            with open(filepath, 'r',encoding='utf-8') as f:
                db.insertFundByJonsData(json.loads(f.read()))

    # 拉最新数据
    # for item in tiantian_indexFundCode:
    #     results = db.selectLatestRecordFromTable(item)
    #     print(item, results)
