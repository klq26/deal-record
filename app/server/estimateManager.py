# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from datetime import timedelta
import grequests
import requests

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
        fullNames = []
        markets = []
        for values in params:
            code = values[0]
            name = values[1]
            fullName = values[2]
            market = values[3]
            if market in [u'沪市', u'深市']:
                marketSymbol = ''
                if market in u'沪市':
                    marketSymbol = '1.'
                else:
                    marketSymbol = '0.'
                urls.append(self.innerUrlPrefix  + marketSymbol + u'{0}&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55&pos=-11&cb=cb'.format(code))
            else:
                urls.append(self.outerUrlPrefix + u'{0}.js'.format(code))
            codes.append(code)
            names.append(name)
            fullNames.append(fullName)
            markets.append(market)

        estimateItems = {}
        navItems = {}

        # 并发
        request_list = [grequests.get(url, headers = self.headers) for url in urls]
        response_list = grequests.map(request_list)
        for i in range(0, len(response_list)):
            response = response_list[i]
            code = codes[i]
            name = names[i]
            fullName = fullNames[i]
            market = markets[i]
            if response.status_code == 200:
                # 解析场外
                if response.url.startswith(self.outerUrlPrefix):
                    text = response.text.replace('jsonpgz(', '').replace(';', '').replace(')', '')
                    if text != u'':
                        jsonData = json.loads(text)
                        del jsonData['fundcode']
                        jsonData['name'] = name
                        jsonData['fullname'] = fullName
                        jsonData['market'] = market
                        estimateItems[code] = jsonData
                    else:
                        navItems[code] = {"name":name, "fullname": fullName, 'market': market}
                # 解析场内
                elif response.url.startswith(self.innerUrlPrefix):
                    text = response.text.replace('cb(', '').replace(';', '').replace(')', '')
                    if text != u'':
                        eastmoneyData = json.loads(text)['data']
                        if eastmoneyData != None:
                            jsonData = {}
                            jsonData['name'] = name
                            jsonData['fullname'] = fullName
                            today = datetime.now().strftime('%Y-%m-%d')
                            yesterday =(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                            jsonData['jzrq'] = yesterday
                            if u'prePrice' in eastmoneyData.keys():
                                jsonData['dwjz'] = str(eastmoneyData['prePrice'])
                            else:
                                jsonData['dwjz'] = u'0.0'
                            details = eastmoneyData['details']
                            if len(details) > 0:
                                latest = details[-1]
                                values = latest.split(',')
                                jsonData['gsz'] = values[1]
                                jsonData['gszzl'] = str(round((float(jsonData['gsz']) / float(jsonData['dwjz']) - 1)*100, 2))
                                jsonData['gztime'] = today + ' ' + values[0][0:5]
                            else:
                                jsonData['gsz'] = jsonData['dwjz']
                                jsonData['gszzl'] = "0.0"
                                jsonData['gztime'] = today + ' ' + '00:00'
                            jsonData['market'] = market
                            estimateItems[code] = jsonData
                        else:
                            navItems[code] = {"name":name, "fullname": fullName, 'market': market}
                    else:
                        navItems[code] = {"name":name, "fullname": fullName, 'market': market}
        # failure
        # https://danjuanapp.com/djapi/fund/000614
        # data.fund_derived.unit_nav
        # 无法估值的品种，再去尝试拿一波净值吧
        #     
        nav_url = u'https://danjuanapp.com/djapi/fund/{0}'
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for key in navItems.keys():
            item = navItems[key]
            response = requests.get(nav_url.format(key), headers=self.headers, verify=False)
            if response.status_code == 200:
                jsonData = json.loads(response.text)
                nav = str(jsonData['data']['fund_derived']['unit_nav'])
                item['dwjz'] = nav
                item['gsz'] = nav
                item['gszzl'] = '0.00'
                item['gztime'] = str(jsonData['data']['fund_derived']['end_date']) + ' 00:00:00'
                item['jzrq'] = str(jsonData['data']['fund_derived']['end_date'])
        # 合并
        result = {'estimate': estimateItems, 'nav': navItems, 'total': len(estimateItems) + len(navItems)}
        # with open(output_path,'w+', encoding='utf-8') as f:
        #     f.write(json.dumps(result, ensure_ascii=False,indent=4))
        return result