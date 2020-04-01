# -*- coding: utf-8 -*-

import os
import sys
import json
from datetime import datetime
from datetime import timedelta
import ssl

from urllib import parse
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup

class dividendInfoSpider:

    def __init__(self):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        self.url_holder = u'http://fundf10.eastmoney.com/fhsp_{0}.html'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
    
    def get(self, codes):
        results = []
        for code in codes:
            print('正在获取 {0} 分红信息..'.format(code))
            response = requests.get(self.url_holder.format(code), headers = self.headers, verify=False)
            if response.status_code == 200:
                htmlText = response.text
                soup = BeautifulSoup(htmlText, 'lxml')
                # 只要分红信息 cfxq
                tables = soup.findAll(lambda e: e.name == 'table' and 'cfxq' in e['class'])
                if len(tables) > 0:
                    table = tables[0]
                    values = table.findAll(lambda  e: e.name == 'td')
                    count = len(values)
                    jsonDict = {'code': code, 'value': []}
                    items = []
                    # count == 1 表示“暂无分红信息!”
                    if count > 5:
                        items = []
                        # 年份	权益登记日	除息日	每份分红	分红发放日
                        for i in range(0, count, 5):
                            itemDict = {}
                            itemDict['年份'] = values[i].contents[0]
                            itemDict['权益登记日'] = values[i+1].contents[0]
                            itemDict['除息日'] = values[i+2].contents[0]
                            itemDict['每份分红'] = values[i+3].contents[0]
                            itemDict['分红发放日'] = values[i+4].contents[0]
                            items.append(itemDict)
                    jsonDict['value'] = items
                    results.append(jsonDict)
        with open(os.path.join(self.folder, 'dividendInfo.json'), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(results, ensure_ascii=False, indent=4))
        pass

if __name__ == "__main__":
    spider = dividendInfoSpider()
    spider.get(['001061','100032','000614'])
    pass