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

from login.requestHeaderManager import requestHeaderManager

class tiantianSpider:

    def __init__(self, strategy = 'klq'):
        # 禁 warning
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        # 当前目录
        self.folder = os.path.abspath(os.path.dirname(__file__))
        if strategy == 'klq':
            self.owner = '康力泉'
            self.headers = requestHeaderManager().getTiantianKLQ()
            self.dateIntervals = self.getDateIntervals()
        elif strategy == 'lsy':
            self.owner = '李淑云'
            self.headers = requestHeaderManager().getTiantianLSY()
            self.dateIntervals = self.getDateIntervals(startYear = 2018, startMonth = 1, startDay = 1)
        # 交易详情 url 数组（后续逐个解析）
        self.detailUrlList = []
        self.results = []
        pass

    def get(self):
        # 获取时间间隔内的交易列表
        for interval in self.dateIntervals:
            htmlText = ''
            folder = os.path.join(self.folder, 'debug', self.owner, 'tradelist')
            tradelist_path = os.path.join(folder, '{0}_{1}_{2}.html'.format(self.owner, interval[0], interval[1]))
            if not os.path.exists(folder):
                os.makedirs(folder)
            if os.path.exists(tradelist_path):
                with open(tradelist_path, 'r', encoding='utf-8') as f:
                    htmlText = f.read()
            else:
                htmlText = self.getTradeListOfInterval(interval)
            [self.detailUrlList.append(x) for x in self.getDetailUrlsFromTradeList(htmlText)]
        # print(len(self.detailUrlList))
        # 获取每一条详情数据
        length = len(self.detailUrlList)
        # length = 15
        for i in range(0, length):
            detailUrl = self.detailUrlList[i]
            htmlText = ''
            # 取 url 中的 id 作为文件名称
            params = parse.parse_qs(parse.urlparse(detailUrl).query)
            id = params['id'][0]
            folder = os.path.join(self.folder, 'debug', self.owner, 'detail')
            detailinfo_path = os.path.join(folder, '{0}_{1}_{2}.html'.format(str(i + 1).zfill(5), self.owner, id))
            if not os.path.exists(folder):
                os.makedirs(folder)
            if os.path.exists(detailinfo_path):
                with open(detailinfo_path, 'r', encoding='utf-8') as f:
                    htmlText = f.read()
            else:
                response = requests.get(detailUrl, headers = self.headers, verify=False)
                if response.status_code == 200:
                    htmlText = response.text
                    with open(detailinfo_path, 'w+', encoding='utf-8') as f:
                        f.write(htmlText)
            jsonData = self.getDetailInfo(htmlText, detailUrl)
            self.results.append(jsonData)
        # [print(x, type(x)) for x in self.results]
        # 写入输出
        output_path = os.path.join(self.folder, 'output', '{0}_record.json'.format(self.owner))
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(self.results, ensure_ascii = False, indent = 4))
        pass

    # 根据今天日期和起始日期,生成多个 90 天时间间隔的二维数组
    def getDateIntervals(self, startYear = 2016, startMonth = 5, startDay = 1, interval = 90):
        dateIntervals = []
        # 起始日期为开户日
        startDate = datetime(year = startYear, month = startMonth, day = startDay)
        # 间隔 90 天
        interval_days = timedelta(days = interval)
        # 和起始日间隔 90 天后的日期
        endDate = startDate + interval_days
        # 终止日期为今天
        today = datetime.now()
        # 字符串格式化
        fmt = '%Y-%m-%d'
        while max(today, endDate) == today:
            # print(startDate.strftime(fmt), endDate.strftime(fmt))
            dateIntervals.append([startDate.strftime(fmt), endDate.strftime(fmt)])
            startDate = endDate + timedelta(days=1)
            endDate = startDate + interval_days
        # 最后一条不足 90 天的数据
        startDate = endDate - interval_days
        endDate = today
        # print(startDate.strftime(fmt), endDate.strftime(fmt))
        dateIntervals.append([startDate.strftime(fmt), endDate.strftime(fmt)])
        return dateIntervals

    # 获取历史交易列表（debug 会保存数据）
    def getTradeListOfInterval(self, interval):
        url = u'https://query.1234567.com.cn/Query/DelegateList?DataType=1&StartDate={0}&EndDate={1}&BusType=0&Statu=0&Account=&FundType=0&PageSize=500&PageIndex=1'
        response = requests.post(url.format(interval[0], interval[1]), headers = self.headers, verify=False)
        if response.status_code == 200:
            folder = self.folder, 'debug', self.owner, 'tradelist'
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(os.path.join(folder, '{0}_{1}_{2}.html'.format(self.owner, interval[0], interval[1])), 'w+', encoding='utf-8') as f:
                f.write(response.text)
            return response.text
        else:
            print('[ERROR] CODE:{0} URL:{1}'.format(response.status_code, url))

    # 整合所有的交易列表，生成详情 url 集合
    def getDetailUrlsFromTradeList(self, htmlText):
        detail_url_list = []
        detail_url_prefix = u'https://query.1234567.com.cn'
        soup = BeautifulSoup(htmlText, 'lxml')
        results = soup.findAll(lambda e: e.name == 'a' and '详情' in e.text)
        # 接口拿回来默认是时间倒叙的
        results = list(reversed(results))
        [detail_url_list.append(detail_url_prefix + x['href']) for x in results]
        return detail_url_list

    def getDetailInfo(self, htmlText, url):
        soup = BeautifulSoup(htmlText, 'lxml')
        results = soup.findAll('div',{'class':'ui-confirm'})
        
        applyInfo_keys = ['applyDate','applyOperate','applyStatus']
        confirmInfo_keys = ['fundName', 'fundCode', 'confirmDate', 'confirmOperate', 'confirmStatus', 'confirmNavUnit', 'confirmNavAcc', 'confirmMoney', 'confirmVolume', 'fee']
        
        jsonData = {'申请信息': {}, '确认信息': {}, '详情页': url }
        # 申请日期（拿累计净值）
        applyDate = ''
        for x in results:
            h3_array = x.select('h3')
            # 结果
            values = []
            if len(h3_array) > 0 and h3_array[0].text == u'申请信息':
                if len(x.select('table')) > 0:
                    # 所有值
                    tags = x.select('table')[0].tbody.findAll('td')
                    # 不要“申请数额”
                    tags.pop(-2)
                    # 不要“标题<br/>代码”
                    tags.pop(1)
                    [values.append(x.text) for x in tags]
                    jsonData['申请信息'] = (dict(zip(applyInfo_keys, values)))
                    applyDate = jsonData['申请信息']['applyDate']
            if len(h3_array) > 0 and h3_array[0].text == u'确认信息':
                if len(x.select('table')) > 0:
                    # 所有值
                    tags = x.select('table')[0].tbody.findAll('td')
                    # “标题<br/>代码”
                    a = tags.pop(1).a
                    # 标题
                    values.append(a.contents[0])
                    # 代码
                    values.append(a.contents[2])
                    [values.append(x.text) for x in tags]
                    # 拿一下累计净值
                    values.insert(6, '待实现')
                    jsonData['确认信息'] = (dict(zip(confirmInfo_keys, values)))
        return jsonData

    
        # with open(os.path.join(os.getcwd(),'{0}_record.html'.format(self.owner)), 'w+', encoding='utf-8') as f:
        # length = len(detail_url_list)
        # length = 5
        # for i in range(0, length):
        #     detail_url = detail_url_list[i]
        #     print(detail_url)
        #     detailInfo = getDetailInfo(detail_url)
        #     f.write('<div>' + '\n')
        #     f.write('<div>交易序号：{0} / {1}</div>'.format(i + 1, length) + '\n')
        #     f.write('<a href=\'{0}\' target=\'_blank\'>{1}</a><br/>'.format(detail_url, detail_url) + '\n')
        #     f.write(detailInfo + '\n')
        #     f.write('</div>' + '\n')
        #     print(detail_url)

        # 拿感兴趣的字段
        # with open(os.path.join(os.getcwd(),'{0}_record.html'.format(self.owner)), 'r', encoding='utf-8') as f:
        #     soup = BeautifulSoup(f.read(), 'lxml')
        #     results = soup.findAll(lambda e: e.name == 'a' and len(e.contents) >= 3)
        #     [print(x.contents[0] + '\t' + x.contents[2]) for x in results]
                
    # 取 2000 条
    # deal_list_url = u'https://danjuanapp.com/djapi/order/p/list?page=1&size=2000&type=all'
    # # 获取所有的成交记录概述
    # response = requests.get(deal_list_url, headers = self.headers, verify=False)
    # if response.status_code == 200:
    #     with open(os.path.join(os.getcwd(),'danjuan_deal_list.json'), 'w+', encoding='utf-8') as f:
    #         f.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))
    # else:
    #     print(response.status_code)

    # https://query.1234567.com.cn/Query/DelegateList?DataType=1&StartDate=2016-5-1&EndDate=2016-7-1&BusType=0&Statu=0&Account=&FundType=0&PageSize=200&PageIndex=1

    # with open(os.path.join(os.getcwd(),'danjuan_deal_list.json'), 'r', encoding='utf-8') as f:
    #     jsonData = json.loads(f.read())
    #     datalist = jsonData['data']['items']
    #     detail_url = u'https://danjuanapp.com/djapi/order/p/plan/{0}'
    #     for item in datalist:
    #         # "order_id": "1819139915911312513",
    #         # "code": "CSI1019",
    #         # "name": "钉钉宝365天组合",
    #         # "status_desc": "交易成功",
    #         # "action_desc": "卖出",
    #         # "created_at": 1584584824274,
    #         # "title": "钉钉宝365天组合",
    #         unix_ts = int(int(item['created_at'])/1000)
    #         date = str(datetime.fromtimestamp(unix_ts))[0:10]
    #         order_id = item['order_id']
    #         order_info_path = '{0}_{1}_{2}_{3}.json'.format(date, item['name'], item['action_desc'], item['status_desc'])
    #         # 请求
    #         response = requests.get(detail_url.format(item['order_id']), headers = self.headers, verify=False)
    #         if response.status_code == 200:
    #             with open(os.path.join(os.getcwd(), order_info_path), 'w+', encoding='utf-8') as order_output_file:
    #                 order_output_file.write(json.dumps(json.loads(response.text), ensure_ascii=False, indent = 4))

if __name__ == "__main__":
    strategy = 'klq'
    if len(sys.argv) >= 2:
        #
        strategy = sys.argv[1]
    else:
        print(u'[ERROR] 参数不足。需要键入策略编号。\'klq\'：康力泉 \'lsy\'：李淑云')
        exit()
    # 传入配置，开始流程
    spider = tiantianSpider(strategy = strategy)
    spider.get()