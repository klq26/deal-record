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

folder = os.path.abspath(os.path.dirname(__file__))

cm = categoryManager()

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route('/api/family_holding', methods=['GET'])
def getFamilyHolding():
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
    df = cm.category_df
    for x in records:
        code = x['code']
        sub = df[df['基金代码'] == code]
        if len(sub) > 0:
            x['name'] = sub.基金简称.values[0]
        else:
            x['name'] = u'未知简称' + code
    data = json.dumps(records, ensure_ascii=False, indent=4)
    return Response(data, status=200, mimetype='application/json')

@app.route('/api/family_estimate', methods=['GET'])
def getFamilyEstimate():
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
        df = cm.category_df
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
        with open(output_path, 'w+', encoding=u'utf-8') as f:
            f.write(json.dumps(params, ensure_ascii=False, indent=4))
    em = estimateManager()
    data = json.dumps(em.esitmate(params), ensure_ascii=False, indent=4)
    return Response(data, status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
    # getFamilyEstimate()