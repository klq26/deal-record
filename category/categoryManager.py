# -*- coding: utf-8 -*-
import os
import sys
import json

import pandas as pd

class categoryManager:

    def __init__(self):
        folder = os.path.abspath(os.path.dirname(__file__))
        self.xlsx_path = os.path.join(folder, u'资产配置分类表.xlsx')
        self.category_df = pd.read_excel(self.xlsx_path)
        self.category_df['基金代码'] = [str(x).zfill(6) for x in self.category_df['基金代码'].values]
        pass

    def getCategoryDataFrame(self):
        return self.category_df

    # 获取对应基金的类别代码
    def getCategoryByCode(self, code):
        result = list(self.category_df[self.category_df['基金代码'] == code].values)
        if len(result) > 0:
            result = result[0]
            return {'category1': result[2], 'category2': result[3], 'category3': result[4], 'categoryId': result[5]}
        else:
            print('[ERROR] {0} 不在资产配置列表中. 请添加'.format(code))
            if sys.platform.startswith('win'):
                os.startfile('https://qieman.com/funds/{0}'.format(code))
                os.startfile(self.xlsx_path)
            exit(1)
            return {}
    