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


# # 遍历代码拿数据
# for code in fund_codes:
#     datalist = []
#     response = requests.get(url_holder.format(code, 1),headers = headers, verify=False)
#     if response.status_code == 200:
#         # 正则表达式
#         re_pattern = r"/\*.*?\*/\ncallback\((.*?)\)"
#         regex  = re.compile(re_pattern)
#         result = regex.findall(response.text)
#         # 取 json
#         jsonData = json.loads(result[0])
#         # 取出总数
#         totalCount = int(jsonData['result']['data']['total_num'])
#         # 算出页码
#         pageCount = 0
#         remainder = totalCount % 20
#         if remainder > 0:
#             pageCount = int(totalCount / 20) + 1
#         else:
#             pageCount = int(totalCount / 20)
#         # 开始行动！
#         print('{0} {1} 总个数：{2} 总页数：{3}'.format(code, '名称待实现', totalCount, pageCount))
#         pageCount = 5
#         for i in range(1, pageCount + 1):
#             response = requests.get(url_holder.format(code, i),headers = headers, verify=False)
#             if response.status_code == 200:
#                 # 正则表达式
#                 re_pattern = r"/\*.*?\*/\ncallback\((.*?)\)"
#                 regex  = re.compile(re_pattern)
#                 result = regex.findall(response.text)
#                 # 取 json
#                 jsonData = json.loads(result[0])
#                 # last one
#                 lastOne = {}
#                 if len(datalist) > 0:
#                     lastOne = datalist[-1]
#                     if len(jsonData['result']['data']['data']) > 0:
#                         firstOne = jsonData['result']['data']['data'][0]
#                         if item['fbrq'][0:10] == lastOne[u'日期']:
#                             # print(item, '重复')
#                             # 去掉重复项
#                             datalist.pop(-1)
#                 for item in jsonData['result']['data']['data']:
#                     datalist.append({'日期':item['fbrq'][0:10], '单位净值':item['jjjz'],'累计净值':item['ljjz']})
#             print('\r{0}%'.format(round(i / pageCount * 100, 2)), end='', flush=True)
#             # 间隔，防止被 Ban
#             time.sleep(0.5)
#         datalist = list(reversed(datalist))
#         [print(x) for x in datalist]
#         with open(os.path.join(os.getcwd(),code + '.json'),'w+',encoding='utf-8') as f:
#             f.write(json.dumps({'code': code, 'name':'待实现', 'data':datalist}, ensure_ascii=False, indent = 4))

class sinaNavSpider:
    
    def __init__(self):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    
    def getNav(code, dateStr):
        # 链接
        url_holder = u'https://stock.finance.sina.com.cn/fundInfo/api/openapi.php/CaihuiFundInfoService.getNav?callback=callback&symbol={0}&page={1}'
        # UA
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'accept-encoding': 'gzip, deflate, br'}


