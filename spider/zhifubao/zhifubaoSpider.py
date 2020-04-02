# -*- coding: utf-8 -*-

import os
import sys
import json
import pandas as pd

class zhifubaoSpider:

    def __init__(self):
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.owner = '康力泉'
    
    # 获取数据
    def get(self):
        return self.load()

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
            df.to_csv(os.path.join(self.folder, 'output', '{0}-zhifubao-unique-codes.csv'.format(self.owner)), sep='\t')
            return df
    
    def load(self):
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.loads(f.read())