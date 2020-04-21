# -*- coding: utf-8 -*-

import os
import sys
import json

from flask import Flask
from flask import request
from flask import Response
# 跨域
from flask_cors import *

from category.categoryManager import categoryManager
from database.fundDBHelper import fundDBHelper
from app.server.holdingDBHelper import *
from app.server.estimateManager import estimateManager

from app.server.cacheManager import cacheManager
from app.server.datetimeManager import datetimeManager

folder = os.path.abspath(os.path.dirname(__file__))

categoryManager = categoryManager()
cm = cacheManager()
dm = datetimeManager()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# 添加公共返回值
def packDataWithCommonInfo(isCache = False, isSuccess = True, msg = "success", duration = '0', data = {}):
    code = 0
    if not isSuccess:
        code = -1
    result = {'code' : code, 'msg' : msg, 'isCache' : False, 'aliyun_date' : datetimeManager().getDateTimeString(), 'data' : data, 'duration' : duration}
    return json.dumps(result, ensure_ascii=False, indent=4, sort_keys=True)

@app.route('/familyholding/api/fundholding', methods=['GET'])
def getFundHolding():
    start_ts = datetimeManager().getTimeStamp()
    # 缓存
    if cm.cacheAvailable(start_ts, request.path):
        data = cm.getCache(start_ts, request.path)
        return Response(data, status=200, mimetype='application/json')
    db = holdingDBHelper()
    records = []
    records = db.selectAllCombineFundHoldings()
    # 基金简称
    df = categoryManager.category_df
    for x in records:
        code = x['code']
        sub = df[df['基金代码'] == code]
        if len(sub) > 0:
            x['name'] = sub.基金简称.values[0]
            x['full_name'] = sub.基金名称.values[0]
        else:
            x['name'] = u'未知 ' + code
            x['full_name'] = u'未知 ' + code
    # data = json.dumps(records, ensure_ascii=False, indent=4)
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = records)
    cm.saveCache(request.path, data)
    return Response(data, status=200, mimetype='application/json')

@app.route('/familyholding/api/accountholding', methods=['GET'])
def getAccountHolding():
    start_ts = datetimeManager().getTimeStamp()
    # 缓存
    if cm.cacheAvailable(start_ts, request.path):
        data = cm.getCache(start_ts, request.path)
        return Response(data, status=200, mimetype='application/json')
    db = holdingDBHelper()
    records = []
    records = db.selectAllIsolatedFundHoldings()
    # 基金简称
    df = categoryManager.category_df
    for x in records:
        code = x['code']
        sub = df[df['基金代码'] == code]
        if len(sub) > 0:
            x['name'] = sub.基金简称.values[0]
            x['full_name'] = sub.基金名称.values[0]
        else:
            x['name'] = u'未知 ' + code
            x['full_name'] = u'未知 ' + code
    # data = json.dumps(records, ensure_ascii=False, indent=4)
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = records)
    cm.saveCache(request.path, data)
    return Response(data, status=200, mimetype='application/json')

@app.route('/familyholding/api/estimate', methods=['GET'])
def getFamilyEstimate():
    start_ts = datetimeManager().getTimeStamp()
    # 缓存
    if cm.cacheAvailable(start_ts, request.path):
        data = cm.getCache(start_ts, request.path)
        return Response(data, status=200, mimetype='application/json')
    # TODO 后面这里弄个缓存，1 天之内都不走数据库了
    output_path = os.path.join(folder, u'app',u'server', u'cache', 'codelist.json')
    params = []
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        # 读缓存
        with open(output_path, 'r', encoding=u'utf-8') as f:
            params = json.loads(f.read())
    else:
        db = holdingDBHelper()
        records = db.selectAllCombineFundHoldings()
        # 基金简称
        df = categoryManager.category_df
        for x in records:
            values = []
            code = x['code']
            sub = df[df['基金代码'] == code]
            if len(sub) > 0:
                name = sub.基金简称.values[0]
                fullName = sub.基金名称.values[0]
                market = sub.市场.values[0]
            else:
                name = u'未知 ' + code
                fullName = sub.基金名称.values[0]
                market = u'其他'
            values = [code, name, fullName, market]
            params.append(values)
        # 后面采用新缓存机制
        # with open(output_path, 'w+', encoding=u'utf-8') as f:
        #     f.write(json.dumps(params, ensure_ascii=False, indent=4))
    em = estimateManager()
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = em.esitmate(params))
    cm.saveCache(request.path, data)
    return Response(data, status=200, mimetype='application/json')

def getFundHoldingPieInfos(code):
    db = holdingDBHelper()
    records = db.selectFundHoldingsGroupByAccount(code)
    results = {}
    total_holding_money = 0.0
    total_holding_volume = 0.0
    for x in records:
        record = {k: v for k, v in x.items() if k not in ['id','date','name','status','holding_nav']}
        total_holding_money += record['holding_money']
        total_holding_volume += record['holding_volume']
        sumItem = None
        if u'母' in x['account']:
            if u'lsy' not in results.keys():
                results['lsy'] = record
            else:
                sumItem = results['lsy']
        elif u'父' in x['account']:
            if u'ksh' not in results.keys():
                results['ksh'] = record
            else:
                sumItem = results['ksh']
        else:
            if u'klq' not in results.keys():
                results['klq'] = record
            else:
                sumItem = results['klq']
        if sumItem != None:
            sumItem['holding_volume'] += record['holding_volume']
            sumItem['holding_money'] += record['holding_money']
            sumItem['holding_gain'] += record['holding_gain']
            sumItem['history_gain'] += record['history_gain']
            sumItem['total_cash_dividend'] += record['total_cash_dividend']
            sumItem['total_fee'] += record['total_fee']
            if record['account'] not in sumItem['account']:
                sumItem['account'] = sumItem['account'] + ',' + record['account']
    
    # format
    for k, v in results.items():
        v['holding_volume'] = round(float(v['holding_volume']), 2)
        v['holding_money'] = round(float(v['holding_money']), 2)
        v['holding_gain'] = round(float(v['holding_gain']), 2)
        v['history_gain'] = round(float(v['history_gain']), 2)
        v['total_cash_dividend'] = round(float(v['total_cash_dividend']), 2)
        v['total_fee'] = round(float(v['total_fee']), 2)
        v['holding_volume_rate'] = round(v['holding_volume'] / total_holding_volume, 4)
        v['holding_money_rate'] = round(v['holding_money'] / total_holding_money, 4)
    [print(k, v) for k,v in results.items()] 

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    # getFundHoldingPieInfos('100032')
    # x = fundDBHelper().selectFundInfo('510050')
    # if x != None:
    #     [print(y) for y in x.items()]
    # print()
    # x = fundDBHelper().selectDividendInfo('510050')
    # [print(y) for y in x]
    # print()
    # x = fundDBHelper().selectSplitInfo('510050')
    # [print(y) for y in x]