    # -*- coding: utf-8 -*-

# 根据数据库返回的值数组，生成对象
def dealRecordModelFromValues(values):
    keys = dealRecordModelKeys()
    model = dealRecordModel()
    modelDict = dict(zip(keys, values))
    model.__dict__ = modelDict
    return model

# 返回模型需要的字段键数组
def dealRecordModelKeys():
    return ['id', 'date', 'code', 'name', 'dealType', 'nav_unit', 'nav_acc', 'volume', 'dealMoney', 'fee', 'occurMoney', 'account', 'category1', 'category2', 'category3', 'categoryId', 'note']

class dealRecordModel:
    """
    成交记录
    """
    def __init__(self, data = None):
        # 流水号
        self.id = '000'
        # 交易日期
        self.date = '2020/01/01'
        # 代码
        self.code = u'000000'
        # 名称
        self.name = u'默认名称'
        # 当前净值
        self.nav_unit = 0.0000
        # 累计净值
        self.nav_acc = 0.0000
        # 成交份额
        self.volume = 0.00
        # 发生金额 or 过手金额（买入多花，卖出少得。买入时等于 净值 * 份额 + fee。卖出时等于 净值 * 份额 - fee。）
        self.occurMoney = 0.00
        # 手续费
        self.fee = 0.00
        # 实际交易金额（deal = total - fee）
        self.dealMoney = 0.00
        # 交易类型：买入，卖出，分红
        self.dealType = '买入'
        # 交易账户
        self.account = '华泰证券'
        # 自定义类别，便于筛选汇总
        self.category1 = '类别1'
        self.category2 = '类别2'
        self.category3 = '类别3'
        self.categoryId = '类别Id'
        # 详细说明
        self.note = '详细说明'
        
        if data:
            self.__dict__ = data

    def __str__(self):
        """
        输出对象
        """
        return str(self.__dict__)
    
    def __getitem__(self, key):
        return getattr(self, key)
    
    def __setitem__(self, key, value):
        setattr(self,key,value)