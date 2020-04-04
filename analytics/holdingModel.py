# -*- coding: utf-8 -*-

import os
import sys
import json
from copy import deepcopy

import pandas as pd

from spider.common.dealRecordModel import *
from category.categoryManager import categoryManager

class holdingModel:
    """
    累进式处理单只基金的成交实录。
    通过第一条成交记录以 initWithDealRecord 进行初始化。
    然后后面每次使用 calcWithDealRecord 对当前对象进行修正。
    最后调用 finish 完成历史收益率的修正。
    """
    def __init__(self):
        # 最后交易日期
        self.date = '2020/01/01'
        # 代码
        self.code = u'000000'
        # 名称
        self.name = u'默认名称'
        # 摊薄净值
        self.holding_nav = 0.0000
        # 持仓份额
        self.holding_volume = 0.00
        # 持仓金额
        self.holding_money = 0.00
        # 持仓已兑现盈亏（会影响显示的摊薄净值，和平均买入成本的差别就在这里）
        self.holding_gain = 0.00
        # 历史清仓盈亏（是之前清仓过的意思，净值等数据重新计算）
        self.history_gain = 0.00
        # 交易以来的总手续费
        self.total_fee = 0.00
        # 买入手续费
        self.buy_fee = 0.00
        # 卖出手续费
        self.sell_fee = 0.00
        # 是否场内交易（将影响使用 dealMoney 还是 occurMoney）
        self.isInnerDeal = False
        # 是否清仓状态
        self.isEmpty = True
        # 状态签名
        self.status = '初始化'
        # 自定义类别，便于筛选汇总
        self.category1 = '类别1'
        self.category2 = '类别2'
        self.category3 = '类别3'
        self.categoryId = '类别Id'

    def __str__(self):
        # return u"日期：{0} 代码：{1} 名称：{2} 摊薄净值：{3} 持仓份额：{4} 持仓金额：{5} 持仓交易盈亏：{6} 历史清仓盈亏：{7} 总手续费：{8}".format(self.date, self.code, self.name, self.holding_nav, self.holding_volume, self.holding_money, self.holding_gain, self.history_gain, self.total_fee)
        return self.__dict__

    # 用成交记录初始化
    def initWithDealRecord(self, record):
        if not isinstance(record, dealRecordModel):
            print('[ERROR] 传入对象不是 dealRecordModel 类型：{0}'.format(record))
            exit(1)
        # 初始化
        self.date = record.date
        self.code = record.code
        self.name = record.name
        self.holding_nav = record.nav_unit
        self.holding_volume = record.volume
        if u'华泰' in record.account or u'华宝' in record.account:
            self.isInnerDeal = True
            self.holding_money = record.dealMoney
            self.holding_nav = round(self.holding_nav, 3)
        else:
            self.isInnerDeal = False
            self.holding_money = record.occurMoney
            self.holding_nav = round(self.holding_money / self.holding_volume, 4)
        self.total_fee = round(record.fee, 2)
        self.buy_fee = round(record.fee, 2)
        self.isEmpty = False
        categoryInfo = categoryManager().getCategory(record.code)
        if categoryInfo != {}:
            self.category1 = categoryInfo['category1']
            self.category2 = categoryInfo['category2']
            self.category3 = categoryInfo['category3']
            self.categoryId = categoryInfo['categoryId']

    # 计算新的成交记录对当前持仓信息的影响
    # 摊薄单价 = (∑买入金额-∑卖出金额-∑现金分红-∑强制赎回确认金额)/∑持仓份额
    def calcWithDealRecord(self, record):
        if not isinstance(record, dealRecordModel):
            print('[ERROR] 传入对象不是 dealRecordModel 类型：{0}'.format(record))
            exit(1)
        # if record.code == '510300':
        #     print()
        # 净值精度
        decimal = 4
        self.date = record.date
        money = 0.00
        if self.isInnerDeal:
            money = record.dealMoney
            decimal = 3
        else:
            money = record.occurMoney
        self.total_fee = round(self.total_fee + record.fee, 2)
        # 卖出交易
        if '卖' in record.dealType:
            self.status = '卖出'
            # 计算收益
            gain = round((record.nav_unit - self.holding_nav) * record.volume, 2)
            self.holding_gain = round(self.holding_gain + gain, 2)
            self.sell_fee = self.sell_fee + round(record.fee, 2)
            if self.holding_volume == record.volume:
                # 卖空，更新累计收益
                self.holding_nav = round(0, decimal)
                self.holding_money = round(0, 2)
                self.holding_volume = 0.00
                self.isEmpty = True
                self.history_gain = round(self.history_gain + self.holding_gain, 2)
                self.holding_gain = 0.00
                self.status = '清仓'
            else:
                modify = 0.0
                if self.isInnerDeal:
                    modify = 0.0
                else:
                    # 场外有卖出操作之后，也要用“未清仓总收益 - 卖出手续费”所得的总金额，还算回摊薄净值的金额，这样卖出后，摊薄净值才会上升
                    modify = round(self.holding_gain - self.sell_fee, 2)
                # 卖出
                self.holding_money = round(self.holding_money - money, 2)
                self.holding_volume = round(self.holding_volume - record.volume, 2)
                self.holding_nav = round((self.holding_money + modify) / self.holding_volume, decimal)
        elif '分红' in record.dealType:
            if money == 0:
                # 红利再投资
                self.status = '分额'
                self.holding_volume = round(self.holding_volume + record.volume, 2)
                self.holding_nav = round(self.holding_money / self.holding_volume, decimal)
            elif record.volume == 0:
                # 现金分红
                # 注：通常场内只支持现金分红，因为份额有必须整 100 的限制
                self.status = '分现'
                gain = round(money, 2)
                self.holding_gain = round(self.holding_gain + gain, 2)
                # 现金分红相当于份额没变的卖出，应该用持仓金额减去未清仓之前的全部卖出收益，算出最新摊薄净值
                self.holding_nav = round((self.holding_money - self.holding_gain) / self.holding_volume, decimal)
            else:
                print('[出错了]   {0} {1} 分红数据有误'.format(self.code, self.date))
                exit(1)
        else:
            self.status = '买入'
            self.buy_fee = self.buy_fee + round(record.fee, 2)
            self.holding_money = round(self.holding_money + money, 2)
            self.holding_volume = round(self.holding_volume + record.volume, 2)
            self.holding_nav = round(self.holding_money / self.holding_volume, decimal)
        pass

    def finish(self):
        # 确定处理完毕后，要使用卖出手续费去修正历史收益
        # 说明：
        # 1）买入手续费要算在初始化净值内，这样 money / volume，money 高，所以初始成本会高
        # 2）卖出手续费需要用来修正历史营收，买入手续费则不计入
        if self.history_gain > 0:
            self.history_gain = round(self.history_gain - self.sell_fee, 2)