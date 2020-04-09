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

@app.route('/familyholding/api/holding', methods=['GET'])
def getFamilyHolding():
    start_ts = datetimeManager().getTimeStamp()
    # 缓存
    if cm.cacheAvailable(start_ts, request.path):
        data = cm.getCache(start_ts, request.path)
        return Response(data, status=200, mimetype='application/json')
    db = holdingDBHelper()
    records = []
    type = request.args.get('type', '')
    if not type:
        type = 1
    else:
        type = int(type)
    if type == 1:
        # 为 1 时，默认给出合并基金代码合并版本的记录，比较简约
        records = db.selectAllCombineFundHoldings()
    else:
        # 不为 1 时，默认给出非合并完整版本的记录，比较详细，同估值系统
        records = db.selectAllIsolatedFundHoldings()
    # 基金简称
    df = categoryManager.category_df
    for x in records:
        code = x['code']
        sub = df[df['基金代码'] == code]
        if len(sub) > 0:
            x['name'] = sub.基金简称.values[0]
        else:
            x['name'] = u'未知简称' + code
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
                isInner = sub.市场.values[0] == u'场内'
            else:
                name = u'未知简称' + code
            values = [code, name, isInner]
            params.append(values)
        # 后面采用新缓存机制
        # with open(output_path, 'w+', encoding=u'utf-8') as f:
        #     f.write(json.dumps(params, ensure_ascii=False, indent=4))
    em = estimateManager()
    # data = json.dumps(em.esitmate(params), ensure_ascii=False, indent=4)
    end_ts = dm.getTimeStamp()
    duration = dm.getDuration(start_ts, end_ts)
    data = packDataWithCommonInfo(duration = duration, data = em.esitmate(params))
    cm.saveCache(request.path, data)
    return Response(data, status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    # getFamilyEstimate()