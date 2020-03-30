# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import ssl
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 基金代码
fund_codes = ['100032']


# 遍历代码拿数据

class fundInfoSpider:
    
    def __init__(self):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'accept-encoding': 'gzip, deflate, br'}
        self.folder = os.path.abspath(os.path.dirname(__file__))
    
    def get(self, fund_codes):
        for code in fund_codes:
            detailInfo = self.getFundDetail(code)
            navInfo = self.getFundNav(code, detailInfo['fundName'])
            with open(os.path.join(self.folder, 'fund_data', '{0}_{1}.json'.format(code, detailInfo['fundName'])),'w+',encoding='utf-8') as f:
                f.write(json.dumps({'detailInfo': detailInfo, 'navInfo': navInfo}, ensure_ascii=False, indent = 4))
        pass

    def getFundDetail(self, code):
        urls = [u'https://danjuanapp.com/djapi/fund/{0}', u'https://danjuanapp.com/djapi/fund/detail/{0}']
        resultDict = {}
        response = requests.get(urls[0].format(code), headers = self.headers, verify = False)
        if response.status_code == 200:
            jsonData = json.loads(response.text)['data']
            resultDict['fundCode'] = jsonData['fd_code']
            resultDict['fundName'] = jsonData['fd_name']
            resultDict['foundDate'] = jsonData['found_date']
            resultDict['fundType'] = jsonData['type_desc']
        response = requests.get(urls[1].format(code), headers = self.headers, verify = False)
        if response.status_code == 200:
            jsonData = json.loads(response.text)['data']
            buy = {'feeRate': jsonData['fund_rates']['declare_rate'], 'feeRateDiscount': jsonData['fund_rates']['declare_discount']}
            # 买入信息
            # resultDict['buy']['feeRate'] = 
            # resultDict['buy']['feeRateDiscount'] = 
            resultDict['buy'] = buy
            # 卖出信息
            resultDict['sell'] = jsonData['fund_rates']['withdraw_rate_table']
            # 持有信息
            resultDict['holding'] = jsonData['fund_rates']['other_rate_table']
            # 确认时间
            jsonConfirm = jsonData['fund_date_conf']
            confirm = {
                'buyConfirmDay': jsonConfirm['buy_confirm_date'], 
                'buyQueryDay': jsonConfirm['buy_query_date'], 
                'canCheckGainDay': jsonConfirm['all_buy_days'],
                'sellConfirmDay': jsonConfirm['sale_confirm_date'],
                'sellQueryDay': jsonConfirm['sale_query_date'],
                'moneyBackDay': jsonConfirm['all_sale_days'],
                }
            resultDict['confirm'] = confirm
        # print(json.dumps(resultDict,ensure_ascii=False, indent=4))
        return resultDict

    def getFundNav(self, code, name):
        # 链接
        url_holder = u'https://stock.finance.sina.com.cn/fundInfo/api/openapi.php/CaihuiFundInfoService.getNav?callback=callback&symbol={0}&page={1}'
        datalist = []
        response = requests.get(url_holder.format(code, 1), headers = self.headers, verify=False)
        if response.status_code == 200:
            # 正则表达式
            re_pattern = r"/\*.*?\*/\ncallback\((.*?)\)"
            regex  = re.compile(re_pattern)
            result = regex.findall(response.text)
            # 取 json
            jsonData = json.loads(result[0])
            # 取出总数
            totalCount = int(jsonData['result']['data']['total_num'])
            # 算出页码
            pageCount = 0
            remainder = totalCount % 20
            if remainder > 0:
                pageCount = int(totalCount / 20) + 1
            else:
                pageCount = int(totalCount / 20)
            # 开始行动！
            print('{0} {1} 总个数：{2} 总页数：{3}'.format(code, name, totalCount, pageCount))
            # pageCount = 5
            for i in range(1, pageCount + 1):
                response = requests.get(url_holder.format(code, i),headers = self.headers, verify=False)
                if response.status_code == 200:
                    # 正则表达式
                    re_pattern = r"/\*.*?\*/\ncallback\((.*?)\)"
                    regex  = re.compile(re_pattern)
                    result = regex.findall(response.text)
                    # 取 json
                    jsonData = json.loads(result[0])
                    # last one
                    lastOne = {}
                    if len(datalist) > 0:
                        lastOne = datalist[-1]
                        if len(jsonData['result']['data']['data']) > 0:
                            firstOne = jsonData['result']['data']['data'][0]
                            if firstOne['fbrq'][0:10] == lastOne[u'date']:
                                # print(item, '重复')
                                # 去掉重复项
                                datalist.pop(-1)
                    for item in jsonData['result']['data']['data']:
                        datalist.append({'date':item['fbrq'][0:10], 'navUnit':item['jjjz'],'navAcc':item['ljjz']})
                print('\r{0}%'.format(round(i / pageCount * 100, 2)), end='', flush=True)
                # 间隔，防止被 Ban
                time.sleep(0.5)
            datalist = list(reversed(datalist))
            return datalist
            # [print(x) for x in datalist]
            # with open(os.path.join(os.getcwd(),code + '.json'),'w+',encoding='utf-8') as f:
            #     f.write(json.dumps({'code': code, 'name': name, 'data':datalist}, ensure_ascii=False, indent = 4))
            # pass