# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from datetime import timedelta
import grequests
import requests

def exception_handler(request, exception):
    print("GRequests Failed: ")
    print(exception)

class estimateManager:

    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"}
        # 场外估值
        self.outerUrlPrefix = u'http://fundgz.1234567.com.cn/js/'
        # 场内净值
        self.innerUrlPrefix = u'http://push2.eastmoney.com/api/qt/stock/details/get?secid='
        self.folder = os.path.abspath(os.path.dirname(__file__))

    """
    使用 grequests 3.7.x 版本在阿里云服务器上，莫名其妙出现返回 response 为 None 的情况。增加 exception_handler 后，发现是：
    maximum recursion depth exceeded while calling a Python object

    即达到最大递归错误。观察每次运行 flask 的 warning：

    /home/klq26/flask-venv/lib/python3.7/site-packages/grequests.py:21: 
    MonkeyPatchWarning: Monkey-patching ssl after ssl has already been imported may lead to errors, including RecursionError on Python 3.6.
    It may also silently lead to incorrect behaviour on Python 3.7. Please monkey-patch earlier. 
    See https://github.com/gevent/gevent/issues/1016. 
    Modules that had direct imports (NOT patched): 
    ['urllib3.util.ssl_ (/home/klq26/flask-venv/lib/python3.7/site-packages/urllib3/util/ssl_.py)', 'urllib3.util (/home/klq26/flask-venv/lib/python3.7/site-packages/urllib3/util/__init__.py)']. 

    上面提示，如果在 gevent 给 ssl 打补丁之前，import 了 ssl，则会在 python 3.7 版本下出现诡异的不可见错误。3.6 则是直接 RecursionError。解决方案：

    在 main_flask.py 下引用 requests 模块之前，先按上述 issue 中提到的方式，给 ssl 打 patch。并且在其他 import ssl 的脚步中，也注释掉了 ssl._create_default_https_context = ssl._create_unverified_context
    这个注释掉的内容，是否影响 requests 的使用，暂时不可知，后面继续观察。至此，问题基本解决。（还有 Warning，但是已经不影响使用了）
    """

    def esitmate(self, params):
        # output_path = os.path.join(self.folder, u'cache', 'estimate.json')
        # 测试期间走缓存
        # if os.path.exists(output_path):
        #     with open(output_path,'r', encoding='utf-8') as f:
        #         return json.loads(f.read())
    
        # 设置 url，异步并发请求
        tasks = []
        resps = []
        for item in params:
            if item['market'] in [u'沪市', u'深市']:
                marketSymbol = ''
                if item['market'] in u'沪市':
                    marketSymbol = '1.'
                else:
                    marketSymbol = '0.'
                item['url'] = self.innerUrlPrefix  + marketSymbol + u'{0}&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55&pos=-11&cb=cb'.format(item['code'])
            elif item['market'] in u'货币':
                item['url'] = u'http://www.baidu.com'
            else:
                item['url'] = self.outerUrlPrefix + u'{0}.js'.format(item['code'])
            tasks.append(grequests.get(item['url']))
        response_list = grequests.map(tasks)
        
        estimateItems = {}
        navItems = {}
        
        # 解析
        for i in range(len(response_list)):
            response = response_list[i]
            item = params[i]
            code = item['code']
            name = item['name']
            fullName = item['fullName']
            market = item['market']
            if response and response.status_code == 200:
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
                # 货币基金
                elif response.url.startswith(u'http://www.baidu.com'):
                    today = datetime.now().strftime('%Y-%m-%d')
                    yesterday =(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    estimateItems[code] = {"dwjz": "1.0000", "fullname": fullName, "gsz": "1.0000", "gszzl": "0.00", "gztime": today + ' ' + '00:00', "jzrq": yesterday, "market": market, "name": name}

        # failure
        # https://danjuanapp.com/djapi/fund/000614
        # data.fund_derived.unit_nav
        # 无法估值的品种，再去尝试拿一波净值吧
        #     
        nav_url = u'https://danjuanapp.com/djapi/fund/{0}'
        # nav_url = u'http://www.baidu.com'
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nav_urls = []
        nav_requests = []
        for key in navItems.keys():
            item = navItems[key]
            item['url'] = nav_url.format(key)
            nav_requests.append(grequests.get(item['url'], headers = self.headers))
        nav_responses = grequests.map(nav_requests, exception_handler=exception_handler)

        for response in nav_responses:
            if response and response.status_code == 200:
                jsonData = json.loads(response.text)
                nav = str(jsonData['data']['fund_derived']['unit_nav'])
                code = jsonData['data']['fd_code']
                item = navItems[code]
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