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

from database.fundDBHelper import fundDBHelper

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
            response = requests.get(self.url_holder.format(code), headers = self.headers, verify=False)
            if response.status_code == 200:
                htmlText = response.text
                soup = BeautifulSoup(htmlText, 'lxml')
                # 标题
                title = '未知'
                titles = soup.findAll(lambda e: e.name == 'a' and code in e.text)
                if len(titles) > 0:
                    title = titles[0].text.split(' ')[0]
                print('正在获取 {0} {1} 的分红信息..'.format(code, title))
                jsonDict = {'代码': code, '名称': title, '分红': [], '拆分': []}
                # 分红信息 cfxq
                tables = soup.findAll(lambda e: e.name == 'table' and 'cfxq' in e['class'])
                if len(tables) > 0:
                    table = tables[0]
                    values = table.findAll(lambda  e: e.name == 'td')
                    count = len(values)
                    items = []
                    # count == 1 表示“暂无分红信息!”
                    if count >= 5:
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
                    jsonDict['分红'] = items
                print('正在获取 {0} {1} 的拆分信息..'.format(code, title))
                # 拆分信息 fhxq（好像网站 class name 的分红和拆分给反了）
                tables = soup.findAll(lambda e: e.name == 'table' and 'fhxq' in e['class'])
                if len(tables) > 0:
                    table = tables[0]
                    values = table.findAll(lambda  e: e.name == 'td')
                    count = len(values)
                    items = []
                    # count == 1 表示“暂无分红信息!”
                    if count >= 4:
                        items = []
                        # 年份	拆分折算日	拆分类型	拆分折算比例
                        for i in range(0, count, 4):
                            itemDict = {}
                            itemDict['年份'] = values[i].contents[0]
                            itemDict['拆分折算日'] = values[i+1].contents[0]
                            itemDict['拆分类型'] = values[i+2].contents[0]
                            itemDict['拆分折算比例'] = values[i+3].contents[0]
                            items.append(itemDict)
                    jsonDict['拆分'] = items
                results.append(jsonDict)
        with open(os.path.join(self.folder, 'dividendInfo.json'), 'w+', encoding='utf-8') as f:
            f.write(json.dumps(results, ensure_ascii=False, indent=4))
        pass

    def insertToDB(self):
        with open(os.path.join(self.folder, 'dividendInfo.json'), 'r', encoding='utf-8') as f:
            db = fundDBHelper()
            datalist = json.loads(f.read())
            for data in datalist:
                db.insertFundDividendByJonsData(data)

if __name__ == "__main__":
    spider = dividendInfoSpider()
    spider.get(['001061','100032','161725'])
    pass