# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from datetime import timedelta
import traceback

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
import grequests

from category.categoryManager import categoryManager

class evalManager:

    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.cm = categoryManager()
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 需要忽略的三级分类
        category3_skips = ['股票', '房地产', '信息科技', '美元债', '无息外借款', '住房公积金', '民间借贷', '企业借贷', '货币基金']
        # 库中三级分类
        category3_uniques = list(self.cm.category_df['三级分类'].unique())
        for item in category3_skips:
            if item in category3_uniques:
                category3_uniques.pop(category3_uniques.index(item))
        self.category3_uniques = category3_uniques
        # print(self.category3_uniques)

        self.results = []
        # 占位填充
        for i in range(len(self.cm.category3_ext_df)):
            item = self.cm.category3_ext_df.values[i]
            index = {}
            index['category1_name'] = self.cm.category3_ext_df['一级分类'].values[i]
            index['category3_name'] = self.cm.category3_ext_df['三级分类'].values[i]
            index['eval_name'] = self.cm.category3_ext_df['蛋卷估值名'].values[i]
            index['code'] = self.cm.category3_ext_df['指数代码'].values[i]
            # 指数点位
            index['current'] = 0.0
            index['change_value'] = 0.0
            index['change_rate'] = "0.00%"
            # 指数估值
            index["pe"] = 0.0
            index["pb"] = 0.0
            index["pe_percentile"] = 0.0
            index["pb_percentile"] = 0.0
            index["roe"] = 0.0
            index["yeild"] = 0.0
            # index["bond_yeild"] = 0.0
            index["peg"] = 0.0
            # index["pb_over_history"] = 0.0
            # index["pe_over_history"] = 0.0
            index['sequence'] = i+1
            # print(index)
            self.results.append(index)
        # [print(x) for x in self.results]

    def getEvals(self):
        """
        获取三级分类的品类的指数估值数据
        """
        url = u'https://danjuanapp.com/djapi/index_eva/dj'
        # category3: 蛋卷估值名称
        response = requests.get(url, headers = self.headers, verify=False)
        if response and response.status_code == 200:
            try:
                datalist = json.loads(response.text)['data']['items']
                eval_names = [x['name'] for x in datalist]
                # print(eval_names)
                """
                ['标普价值', '中证银行', '红利低波', '上证红利', '300红利LV', '中证红利', '红利成长LV', '300价值', '中证煤炭', '国证地产', '香港大盘', '国企指数', '基本面50', '央视50', '恒生指数', '标普红利', '神奇公式', '上证50', '上证180', '中证100', '东证竞争', '沪深300', '香港中小', '标普质量', '深证红利', 'MSCI印度', '中证500', '中概互联50', '中证1000', '中证军工', '新能源车', '国证A指', '基本面60', '基本面120', '德国DAX', '养老产业', '标普500', '深证100', '纳指100', '中证环保', '深证成指', '证券公司', '全指可选', '主要消费', '中证白酒', '食品饮料', '中国互联', 'TMT50', '医药100', '中证电子', '中证传媒', '全指医药', '创业板', '全指信息', '中证医疗', '50AH优选', 'MSCI中国', '500低波', '5G通讯', '科技龙头']
                """
                for item in self.results:
                    if item['eval_name'] in eval_names:
                        val = [x for x in datalist if x['name'] == item['eval_name']][0]
                        item["pe"] = val.get("pe", 0.00)
                        item["pb"] = val.get("pb", 0.00)
                        item["pe_percentile"] = val.get("pe_percentile", 0.00)
                        item["pb_percentile"] = val.get("pb_percentile", 0.00)
                        item["roe"] = val.get("roe", 0.00)
                        item["yeild"] = val.get("yeild", 0.00)
                        # item["bond_yeild"] = val.get("bond_yeild", 0.00)
                        item["peg"] = val.get("peg", 0.00)
                        # item["pb_over_history"] = val.get("pb_over_history", 0.00)
                        # item["pe_over_history"] = val.get("pe_over_history", 0.00)
            except Exception as e:
                print('getEvals exception:\n')
                traceback.print_exc()
        # [print(x) for x in self.results]
        
    def getIndexValues(self, xueqiu_indexs_path):
        """
        获取三级分类的品类的指数点数数据
        """
        # 从多接口中，提取需要用来估值的指数信息
        category3_indexs = list(self.cm.category3_ext_df['指数代码'].unique())
        # print(category3_indexs)
        aliyun_host = 'https://www.klq26.site/'
        china = aliyun_host + 'marketinfo/api/indexs/china'
        asian = aliyun_host + 'marketinfo/api/indexs/asian?sort=2'
        euro = aliyun_host + 'marketinfo/api/indexs/euro?sort=2'
        america = aliyun_host + 'marketinfo/api/indexs/america?sort=2'
        goods = aliyun_host + 'marketinfo/api/goods_and_exchanges'
        urls = [china, asian, euro, america, goods]
        index_requests = [grequests.get(url, headers = self.headers) for url in urls]
        index_responses = grequests.map(index_requests, exception_handler=self.exception_handler)
        for resp in index_responses:
            if resp and resp.status_code == 200:
                # {
                #     "name": "基本面60",
                #     "code": "SZ399701",
                #     "current": 9055.37,
                #     "change_value": 23.82,
                #     "change_rate": "0.26%"
                # },
                datalist = None
                if resp.url.endswith('goods_and_exchanges'):
                    datalist = json.loads(resp.text)['data']['goods']
                else:
                    datalist = json.loads(resp.text)['data']
                for item in datalist:
                    if item['indexCode'] in category3_indexs:
                        sequence = category3_indexs.index(item['indexCode'])
                        index = self.results[sequence]
                        index['current'] = item['current']
                        index['change_value'] = item['dailyChangValue']
                        index['change_rate'] = item['dailyChangRate']
        # 补雪球数据（selenium 每 3 分钟更新一次）
        with open(xueqiu_indexs_path,'r',encoding=u'utf-8') as f:
            datalist = json.loads(f.read())
            for item in datalist:
                sequence = category3_indexs.index(item['code'])
                index = self.results[sequence]
                index['current'] = item['current']
                index['change_value'] = item['change_value']
                index['change_rate'] = item['change_rate']
        # results.sort(key=lambda x:x['sequence'])
        # [print(x) for x in self.results]

    def exception_handler(self, request, exception):
        print("GRequests Failed: ")
        print(exception)

if __name__ == "__main__":
    evalManager = evalManager()
    evalManager.getEvals()