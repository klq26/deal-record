# -*- coding: utf-8 -*-
import os
import sys
import json
import ssl
from datetime import datetime
from datetime import timedelta
from database.fundDBHelper import fundDBHelper
from fundInfoSpider import fundInfoSpider

class fundNavUpdater:
    
    def __init__(self):
        self.db = fundDBHelper()
        self.infoSpider = fundInfoSpider()
        pass

    def update(self):
        codes = self.db.selectAllFundNavCodes()
        for code in codes:
            result = self.db.selectLatestRecordFromFundNavTable(code)
            lastDate = datetime.strptime(result[0], '%Y-%m-%d')
            # 比最新记录多一天
            startDate = lastDate + timedelta(days = 1)
            # print('latest {0} start {1}'.format(lastDate, startDate))
            self.updateNav(code, startDate = startDate)

    def updateNav(self, code, startDate):
        # 字符串格式化
        fmt = '%Y-%m-%d'
        # 终止日期为今天
        today = datetime.now()
        if startDate > today:
            print('[ERROR] 起始日期比今天更靠后。start：{0} today：{1}'.format(startDate, today))
            return
        startDateStr = startDate.strftime(fmt)
        endDateStr = today.strftime(fmt)
        
        results = self.infoSpider.getFundNavByTime(code, startDateStr, endDateStr)
        for x in results:
            # keys = [] 那边有默认值
            items = []
            items.append(x['date'])
            items.append(x['navUnit'])
            items.append(x['navAcc'])
            self.db.insertDataToTable('nav_{0}'.format(code), keys = [], values = items)

if __name__ == "__main__":
    worker = fundNavUpdater()
    worker.update()
    pass
