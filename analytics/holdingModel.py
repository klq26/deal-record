# -*- coding: utf-8 -*-

import os
import sys
import json

class accountAnalytics:

    def __init__(self, data = None):
        # 交易日期
        self.date = '2020/01/01'
        # 代码
        self.code = u'000000'
        # 名称
        self.name = u'默认名称'
        # 摊薄净值
        self.holding_nav = 0.0000
        # 成交份额
        self.holding_volume = 0.00
        # 发生金额 or 过手金额（买入多花，卖出少得。买入时等于 净值 * 份额 + fee。卖出时等于 净值 * 份额 - fee。）
        self.occurMoney = 0.00
        