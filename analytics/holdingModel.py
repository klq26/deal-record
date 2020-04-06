# -*- coding: utf-8 -*-

import os
import sys
import json
from copy import deepcopy

import pandas as pd

from spider.common.dealRecordModel import *
from category.categoryManager import categoryManager

# 公式
# 持仓单价Pn = (持仓单价Pn-1 * 交易确认前份额 + 买入金额 - 卖出金额 - 现金分红) / (交易前份额 + 买入份额 + 份额再投资 - 赎回份额)

# 摊薄成本 = ∑买入或转入确认金额（含手续费） - ∑卖出或转出确认金额（含手续费） - ∑现金分红 - ∑强制赎回确认金额
# 摊薄单价 = 摊薄成本 / 持仓份额

# 持有收益 = (单位净值 - 摊薄单价) * 持仓份额
# 累计收益 = 当前市值 + 赎回金额 + 现金分红 - 买入金额（含手续费）

# 累计盈亏 = 持仓份额 * 最新净值 - 摊薄成本
# 累计盈亏率 = 累计盈亏 / 摊薄成本

# 个人理解
# 投资过程相当于把钱放入到一个两个袋子中。
# 所有买入和份额分红都是放到袋子 A，当有卖出或现金分红时，拿出一部分放到袋子 B，这部分不再受市场涨跌变化。
# 累计收益最终将是 A 和 B 的市值总和减去投入的所有资金

# 计算累计收益举例
# 例：投资者持 100000 元申购某只基金，申购费率 0.6%，申购份额为 94670.07 份，投资期间现金分红每 10 份分 0.01 元。计算累计收益(估算)当日基金单位净值为 1.1500，则累计收益为：
# ★申购费用 = 100000 - 100000 / (1+0.6%) = 596.42 元
# 现金分红 = 94670.07 / 10 * 0.01 = 94.67 元
# 当前市值 = 1.1500 * 94670.07 = 108870.58 元
# 累计盈亏 = 108870.58 + 0(赎回) + 94.67 - 100000 = 8965.25元

class holdingModel:
    """
    累进式处理单只基金的成交实录。
    通过第一条成交记录以 initWithDealRecord 进行初始化。
    然后后面每次使用 calcWithDealRecord 对当前对象进行修正。
    最后调用 finish 完成历史收益率的修正。
    """
    def __init__(self):
        self.nav_decimal = 4
        self.volume_decimal = 3
        self.money_decimal = 3
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
        # 总现金分红
        self.total_cash_dividend = 0.00
        # 交易以来的总手续费
        self.total_fee = 0.00
        # 买入手续费
        self.buy_fee = 0.00
        # 卖出手续费
        self.sell_fee = 0.00
        # 交易总费用会否影响到网站公布的摊薄净值
        self.isNavContainsTradeFee = False

        self.isNavContiansSellGainAffect = False
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
        return self.__dict__

    def debugBreak(self, record):
        # if u'支付宝' in record.account:
        if '519776' in record.code:
            return True

    # 用成交记录初始化
    def initWithDealRecord(self, record):
        if not isinstance(record, dealRecordModel):
            print('[ERROR] 传入对象不是 dealRecordModel 类型：{0}'.format(record))
            exit(1)
        if self.debugBreak(record):
            print()
        # 初始化
        self.date = record.date
        self.code = record.code
        self.name = record.name
        self.holding_nav = record.nav_unit
        self.holding_volume = record.volume
        # 买入、建仓用 occurMoney（含手续费）
        self.holding_money = record.occurMoney
        # 网站公布摊薄净值所受影响情况列举
        if u'华泰' in record.account or u'华宝' in record.account:
            # 股票账户：含手续费 False 卖出获利修正 False
            self.nav_decimal = 3
            self.isNavContainsTradeFee = False
            self.isNavContiansSellGainAffect = False
            self.holding_nav = round(self.holding_nav, self.nav_decimal)
        elif u'蛋卷' in record.account:
            # 蛋卷：含手续费 False 卖出获利修正 True
            self.nav_decimal = 4
            self.isNavContainsTradeFee = False
            self.isNavContiansSellGainAffect = True
            self.holding_money = round(self.holding_money - record.fee, self.money_decimal)
            self.holding_nav = round(self.holding_money / self.holding_volume, self.nav_decimal)
        elif u'支付宝' in record.account:
            # 支付宝：含手续费 True 卖出获利修正 False
            self.nav_decimal = 4
            self.isNavContainsTradeFee = True
            # 这里姑且是 False，因为没卖过
            self.isNavContiansSellGainAffect = False
            self.holding_nav = round(self.holding_money / self.holding_volume, self.nav_decimal)
        elif u'天天' in record.account:
            # 天天：含手续费 True 卖出获利修正 False
            self.nav_decimal = 4
            self.isNavContainsTradeFee = True
            self.isNavContiansSellGainAffect = False
            self.holding_nav = round(self.holding_money / self.holding_volume, self.nav_decimal)
        elif u'且慢' in record.account:
            # 且慢：含手续费 True 卖出获利修正 True
            self.nav_decimal = 4
            self.isNavContainsTradeFee = True
            self.isNavContiansSellGainAffect = True
            # 刚建仓，holding_money 不需要加上 holding_gain
            self.holding_nav = round(self.holding_money / self.holding_volume, self.nav_decimal)

        self.total_fee = round(record.fee, self.money_decimal)
        self.buy_fee = round(record.fee, self.money_decimal)
        self.isEmpty = False
        categoryInfo = categoryManager().getCategory(record.code)
        if categoryInfo != {}:
            self.category1 = categoryInfo['category1']
            self.category2 = categoryInfo['category2']
            self.category3 = categoryInfo['category3']
            self.categoryId = categoryInfo['categoryId']

    # 计算新的成交记录对当前持仓信息的影响
    # 虽然计算摊薄持仓净值的公式一致，但是网站还是有网站自己的特点：
    # 1. 华宝，华泰，蛋卷这三家公司，公布的摊薄净值忽略了手续费的影响。
    # 2. 天天，且慢两家公司，会把你的总费用，也计入净值。即：买入后，如果第二天净值没变，你持仓收益 = 负手续费。
    # 3. 个人感觉后两者的做法更加透明，不过只要能详细计算，就无所谓了。
    def calcWithDealRecord(self, record):
        if not isinstance(record, dealRecordModel):
            print('[ERROR] 传入对象不是 dealRecordModel 类型：{0}'.format(record))
            exit(1)
        if self.debugBreak(record):
            print()
        if not self.isNavContainsTradeFee:
            self.holding_money = round(self.holding_money - record.fee, self.money_decimal)
        self.date = record.date
        self.total_fee = round(self.total_fee + record.fee, self.money_decimal)
        # 卖出交易
        if '卖' in record.dealType:
            # 卖出时，dealMoney 大于 ouccurMoney（扣除手续费后才是到手）
            # 计算收益盈亏
            gain = round((record.nav_unit - self.holding_nav) * record.volume, self.money_decimal)
            self.holding_gain = round(self.holding_gain + gain, self.money_decimal)
            self.sell_fee = self.sell_fee + round(record.fee, self.money_decimal)
            # 清仓
            if self.holding_volume == record.volume:
                self.status = '清仓'
                self.holding_money = round(0, self.money_decimal)
                self.holding_volume = round(0, self.volume_decimal)
                self.holding_nav = round(0, self.nav_decimal)
                self.isEmpty = True
                self.history_gain = round(self.history_gain + self.holding_gain , self.money_decimal)
                self.holding_gain = 0.00
            else:
                # 部分卖出
                self.status = '卖出'
                gainModify = 0.0
                if self.isNavContiansSellGainAffect:
                    gainModify = self.holding_gain
                self.holding_money = round(self.holding_money - record.dealMoney, self.money_decimal)
                self.holding_volume = round(self.holding_volume - record.volume, self.volume_decimal)
                self.holding_nav = round((self.holding_money + gainModify) / self.holding_volume, self.nav_decimal)
        elif '分红' in record.dealType:
            if record.occurMoney == 0:
                # 红利再投资
                self.status = '分额'
                self.holding_volume = round(self.holding_volume + record.volume, self.volume_decimal)
                self.holding_nav = round((self.holding_money ) / self.holding_volume, self.nav_decimal)
            elif record.volume == 0:
                # 现金分红
                # 注：通常场内只支持现金分红，因为份额有必须整 100 的限制
                self.status = '分现'
                self.total_cash_dividend = round(self.total_cash_dividend + record.occurMoney, self.money_decimal)
                # 现金分红相当于份额没变的卖出，应该用持仓金额减去未清仓之前的全部卖出收益，算出最新摊薄净值
                self.holding_money = round(self.holding_money - record.occurMoney, self.money_decimal)
                gainModify = 0.0
                if self.isNavContiansSellGainAffect:
                    gainModify = self.holding_gain
                self.holding_nav = round((self.holding_money + gainModify) / self.holding_volume, self.nav_decimal)
            else:
                print('[出错了]   {0} {1} 分红数据有误'.format(self.code, self.date))
                exit(1)
        else:
            # 买入时，ouccurMoney（含买入手续费的总金额） 大于 dealMoney
            self.status = '买入'
            self.buy_fee = self.buy_fee + round(record.fee, self.money_decimal)
            self.holding_money = round(self.holding_money + record.occurMoney, self.money_decimal)
            self.holding_volume = round(self.holding_volume + record.volume, self.volume_decimal)
            self.holding_nav = round(self.holding_money / self.holding_volume, self.nav_decimal)
        pass

    def finish(self):
        # 确定处理完毕后，要使用卖出手续费去修正历史收益
        # 说明：
        # 1）买入手续费要算在初始化净值内，这样 money / volume，money 高，所以初始成本会高
        # 2）卖出手续费需要用来修正历史营收，买入手续费则不计入（因为买入手续费已经在买入时就拉高净值了，所以已经起作用了）
        self.holding_gain = round(self.holding_gain + self.total_cash_dividend, self.money_decimal)
        if self.history_gain > 0:
            self.history_gain = round(self.history_gain - self.sell_fee, self.money_decimal)