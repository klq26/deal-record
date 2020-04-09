# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from datetime import timedelta
import grequests

class estimateManager:

    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
        # 场外估值
        self.outerUrlPrefix = u'http://fundgz.1234567.com.cn/js/'
        # 场内净值
        self.innerUrlPrefix = u'http://push2.eastmoney.com/api/qt/stock/details/get?secid='
        self.folder = os.path.abspath(os.path.dirname(__file__))

    def esitmate(self, params):
        # output_path = os.path.join(self.folder, u'cache', 'estimate.json')
        # 测试期间走缓存
        # if os.path.exists(output_path):
        #     with open(output_path,'r', encoding='utf-8') as f:
        #         return json.loads(f.read())
        
        urls = []
        codes = []
        names = []
        for values in params:
            code = values[0]
            name = values[1]
            isInner = values[2]
            if isInner:
                marketSymbol = ''
                if code.startswith('5'):
                    marketSymbol = '1.'
                else:
                    marketSymbol = '0.'
                urls.append(self.innerUrlPrefix  + marketSymbol + u'{0}&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55&pos=-11&cb=cb'.format(code))
            else:
                urls.append(self.outerUrlPrefix + u'{0}.js'.format(code))
            codes.append(code)
            names.append(name)

        successItems = {}
        failureItems = {}

        # 并发
        request_list = [grequests.get(url, headers = self.headers) for url in urls]
        response_list = grequests.map(request_list)
        for i in range(0, len(response_list)):
            response = response_list[i]
            code = codes[i]
            name = names[i]
            if response.status_code == 200:
                # 解析场外
                if response.url.startswith(self.outerUrlPrefix):
                    text = response.text.replace('jsonpgz(', '').replace(';', '').replace(')', '')
                    if text != u'':
                        jsonData = json.loads(text)
                        del jsonData['fundcode']
                        jsonData['name'] = name
                        jsonData['market'] = '场外'
                        successItems[code] = jsonData
                    else:
                        failureItems[code] = {"name":name}
                # 解析场内
                elif response.url.startswith(self.innerUrlPrefix):
                    text = response.text.replace('cb(', '').replace(';', '').replace(')', '')
                    if text != u'':
                        eastmoneyData = json.loads(text)['data']
                        jsonData = {}
                        jsonData['name'] = name
                        today = datetime.now().strftime('%Y-%m-%d')
                        yesterday =(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                        jsonData['jzrq'] = yesterday
                        jsonData['dwjz'] = eastmoneyData['prePrice']
                        details = eastmoneyData['details']
                        if len(details) > 0:
                            latest = details[-1]
                            values = latest.split(',')
                            jsonData['gsz'] = values[1]
                            jsonData['gszzl'] = round((float(jsonData['gsz']) / float(jsonData['dwjz']) - 1)*100, 2)
                            jsonData['gztime'] = today + ' ' + values[0][0:5]
                        else:
                            jsonData['gsz'] = jsonData['dwjz']
                            jsonData['gszzl'] = 0.0
                            jsonData['gztime'] = today + ' ' + '00:00'
                        jsonData['market'] = '场内'
                        successItems[code] = jsonData
                    else:
                        failureItems[code] = {"name":name}
        # 合并
        result = {'success': successItems, 'failure': failureItems, 'total': len(successItems) + len(failureItems)}
        # with open(output_path,'w+', encoding='utf-8') as f:
        #     f.write(json.dumps(result, ensure_ascii=False,indent=4))
        return result

# text = response.text.replace('jsonpgz(', '').replace(';', '').replace(')', '')
# # print(u'[URL]:{0}'.format(self.url.format(code)))
# # print(u'[TEXT]:{0}'.format(text))
# # [TEXT]:{"fundcode":"000478","name":"建信中证500指数增强A","jzrq":"2019-10-25","dwjz":"1.9812","gsz":"2.0151","gszzl":"1.71","gztime":"2019-10-28 15:00"}
# if text == u'':
#     # 华安德国 30 这样的 QDII 基金，可能没有估值，返回一个默认的
#     return(0, 'NA', 0, 0.0000, 'NA')
# data = json.loads(text)
# # 当前净值，当前净值日期，估算净值，估算增长率，估算时间戳
# return (round(float(data['dwjz']), 4), data['jzrq'], round(float(data['gsz']), 4), round(float(data['gszzl'])/100, 4), data['gztime'])

