import os
import sys

from login.account import account
from login.requestHeaderManager import requestHeaderManager
import spider.common.dealRecordModel
from spider.tiantian.tiantianSpider import tiantianSpider

if __name__ == "__main__":
    # 测试系统路径
    # [print(x) for x in sys.path]
    tiantianSpider().get()