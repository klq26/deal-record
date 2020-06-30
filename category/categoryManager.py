# -*- coding: utf-8 -*-
import os
import sys
import json

import pandas as pd

from tools.fundInfoSpider import fundInfoSpider
from tools.dividendInfoSpider import dividendInfoSpider
from database.fundDBHelper import fundDBHelper

class categoryManager:
    """
    自建交易品种分类列表，包含从投资以来，所有交易过的品种。
    支持返回对应代码的分类信息，如果库中不包含一个基金代码，则会运行辅助添加机制：

    1）打开天天基金、且慢网站上该只基金的详情页。
    2）尝试获取基金的历史净值数据和分红、拆分数据，传入阿里云服务器
    3）打开 xlsx 文件。
    """

    def __init__(self):
        folder = os.path.abspath(os.path.dirname(__file__))
        self.xlsx_path = os.path.join(folder, u'资产配置分类表.xlsx')
        self.category_df = pd.read_excel(self.xlsx_path)
        self.category_df['基金代码'] = [str(x).zfill(6) for x in self.category_df['基金代码'].values]
        pass

    def getCategoryDataFrame(self):
        return self.category_df

    # 获取货币基金的虚拟类别
    def getCashFundCategory(self):
        return self.getCategoryByCode('999999')

    # 获取对应基金的类别代码
    def getCategoryByCode(self, code):
        result = list(self.category_df[self.category_df['基金代码'] == code].values)
        if len(result) > 0:
            result = result[0]
            return {'category1': result[3], 'category2': result[4], 'category3': result[5], 'categoryId': result[6]}
        else:
            print('[ERROR] {0} 不在资产配置列表中. 请添加'.format(code))
            if sys.platform.startswith('win'):
                os.startfile('https://qieman.com/funds/{0}'.format(code))
                os.startfile('http://fund.eastmoney.com/{0}.html?spm=search'.format(code))
                os.startfile(self.xlsx_path)
                # 下载基金详情，历史净值
                fundInfos = fundInfoSpider().get([code])
                # 下载分红/拆分信息
                dividends = dividendInfoSpider().get([code])
                # Database
                db = fundDBHelper()
                for info in fundInfos:
                    db.insertFundByJonsData(info)
                for info in dividends:
                    db.insertFundDividendByJonsData(info)
            exit(1)
            return {}
    