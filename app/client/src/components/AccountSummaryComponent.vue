<template>
  <div class="container" @click="showDaily = !showDaily">
    <!-- 估值情况 -->
    <div class="summaryContainer">
      <div class="summaryValueContainer" v-show="showDaily">
        <div class="summaryTitle">日收益</div>
        <div class="summaryValue" :class="textColorWithValue(totalDailyGain)">{{totalDailyGain}}</div>
      </div>
      <div class="summaryRateContainer" v-show="showDaily">
        <div class="summaryTitle">收益率</div>
        <div
          class="summaryValue"
          :class="textColorWithValue(totalDailyGain)"
        >{{(totalDailyGain / (totalFamilyCap - totalDailyGain) * 100).toFixed(2)}}%</div>
      </div>
      <div class="summaryValueContainer" v-show="!showDaily">
        <div class="summaryTitle">总收益</div>
        <div class="summaryValue" :class="textColorWithValue(totalHoldingGain)">{{totalHoldingGain}}</div>
      </div>
      <div class="summaryRateContainer" v-show="!showDaily">
        <div class="summaryTitle">收益率</div>
        <div
          class="summaryValue"
          :class="textColorWithValue(totalHoldingGain)"
        >{{(totalHoldingGain / totalFamilyCap * 100).toFixed(2)}}%</div>
      </div>
    </div>
    <!-- 资金情况 -->
    <div class="sumcontainer" style="margin-bottom:2px;">
      <div class="sumcell" v-for="(item, index) in moneyCategorys" :key="index">
        <div class="moneyCategoryTitle">{{item}}</div>
        <div
          class="moneyCategorySum"
          :class="[moneyCategoryTextColor(index), {flash : isUpdating}]"
        >{{showSummary(index)}}</div>
      </div>
    </div>
    <!-- 分类汇总 -->
    <div class="sumcontainer">
      <div class="sumcell" v-for="item in categorys" :key="item.index">
        <div class="categoryTitle">{{item}}</div>
        <div class="categorySum" :class="textColorWithValue(sum(item))">{{sum(item)}}</div>
      </div>
    </div>
    <!-- 账户收益 -->
    <div
      class="accountCell"
      :class="accountBackground(item)"
      v-for="item in Object.keys(accounts)"
      :key="item.index"
    >
      <div class="title">{{item}}</div>
      <div
        class="today"
        :class="[textColorWithValue(today(item)), {flash : isUpdating}]"
      >{{today(item)}}</div>
      <div
        class="total"
        :class="[textColorWithValue(total(item)), {flash : isUpdating}]"
      >{{total(item)}}</div>
    </div>
    <!-- 三级分类估值 -->
    <div class="category3cell">
      <p class="category3name category3-title">名称</p>
      <!-- 估值 title -->
      <p class="category3-narrow-value category3-title" v-show="showEval">成本</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">指数</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">盈率</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">PE</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">PB</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">ROE</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">PEG</p>
      <p class="category3-narrow-value category3-title" v-show="showEval">股息</p>
      <!-- 市值 title -->
      <p class="category3-middle-value category3-title" v-show="!showEval">日盈亏</p>
      <p class="category3-narrow-value category3-title" v-show="!showEval">日盈比</p>
      <p class="category3-middle-value category3-title" v-show="!showEval">总盈亏</p>
      <p class="category3-narrow-value category3-title" v-show="!showEval">总盈比</p>
      <p class="category3-middle-value category3-title" v-show="!showEval">总市值</p>
      <p class="category3-narrow-value category3-title" v-show="!showEval">总值比</p>
    </div>
    <div class="category3cell" v-for="item in evals" :key="item.index" @click.stop="showEval = !showEval">
      <p class="category3name" :class="categoryColorWithValue(item)">{{item.category3_name}}</p>
      <!-- 估值 -->
      <p class="category3-narrow-value" v-show="showEval">{{category3holdingIndexValue(item)}}</p>
      <p class="category3-narrow-value" v-show="showEval">{{item.current.toFixed(0)}}</p>
      <p class="category3-narrow-value" v-show="showEval" :class="category3GainRateTextColor(item)">{{category3GainRate(item)}}</p>
      <p class="category3-narrow-value" v-show="showEval" :style="evalRankBackground(item.pe_percentile)">{{item.pe.toFixed(1)}}</p>
      <p class="category3-narrow-value" v-show="showEval" :style="evalRankBackground(item.pb_percentile)">{{item.pb.toFixed(1)}}</p>
      <p class="category3-narrow-value" v-show="showEval">{{(item.roe * 100).toFixed(1) + '%'}}</p>
      <p class="category3-narrow-value" v-show="showEval">{{item.peg.toFixed(2)}}</p>
      <p class="category3-narrow-value" v-show="showEval">{{(item.yeild * 100).toFixed(2) + '%'}}</p>
      <!-- 市值 -->
      <p class="category3-middle-value" :class="textColorWithValue(item.daily)" v-show="!showEval">{{item.daily}}</p>
      <p class="category3-narrow-value" :class="textColorWithValue(item.daily ? item.daily : 0)" v-show="!showEval">{{((item.daily ? item.daily : 0) / totalDailyGain * 100).toFixed(1) + '%'}}</p>
      <p class="category3-middle-value" :class="textColorWithValue(item.total)" v-show="!showEval">{{item.total}}</p>
      <p class="category3-narrow-value" :class="textColorWithValue(item.total ? item.total : 0)" v-show="!showEval">{{((item.total ? item.total : 0) / totalHoldingGain * 100).toFixed(1) + '%'}}</p>
      <p class="category3-middle-value" v-show="!showEval">{{item.marketcap ? parseFloat(item.marketcap).toFixed(0) : 0}}</p>
      <p class="category3-narrow-value" v-show="!showEval">{{((item.marketcap ? item.marketcap : 0) / totalMarketCap * 100).toFixed(1) + '%'}}</p>
      <!-- <p class="category3name" v-show="!showEval">{{item.total}}</p>
      <p class="category3name" v-show="!showEval">{{item.marketcap}}</p> -->
    </div>
  </div>
</template>

<script>
export default {
  name: 'AccountSummaryComponent',
  props: ['moneyinfos', 'holdings', 'estimates', 'evals'],
  methods: {
    showSummary (type) {
      switch (type) {
        case 0:
          // 现金类
          return (this.myMoneyInfos.cash.value / 10000).toFixed(2) + ' 万元'
        case 1:
          // 冻结类
          return (this.myMoneyInfos.freeze.value / 10000).toFixed(2) + ' 万元'
        case 2:
          return (this.totalMarketCap / 10000).toFixed(2) + ' 万元'
        case 3:
          var cash = this.myMoneyInfos.cash.value
          var freeze = this.myMoneyInfos.freeze.value
          var fund = parseFloat(this.totalMarketCap)
          this.totalFamilyCap = cash + freeze + fund
          return ((cash + freeze + fund) / 10000).toFixed(2) + ' 万元'
      }
    },
    sum (category1) {
      var total = 0.0
      for (var i in this.myHoldings) {
        var holding = this.myHoldings[i]
        if (holding.category1 === category1) {
          if (this.showDaily) {
            total = total + parseFloat(holding.dailyChange)
          } else {
            total = total + parseFloat(holding.totalChange)
          }
        }
      }
      return total.toFixed(1)
    },
    accountBackground (name) {
      if (name.indexOf('且慢') !== -1) {
        return 'qieman'
      } else if (name.indexOf('天天') !== -1) {
        return 'tiantian'
      } else if (name.indexOf('华宝') !== -1) {
        return 'huabao'
      } else if (name.indexOf('华泰') !== -1) {
        return 'huatai'
      } else if (name.indexOf('支付宝') !== -1) {
        return 'zhifubao'
      } else if (
        name.indexOf('螺丝钉') !== -1 ||
        name.indexOf('钉钉宝') !== -1
      ) {
        return 'danjuan'
      } else {
        return 'unknow'
      }
    },
    today (name) {
      return this.accounts[name]['today'].toFixed(2)
    },
    total (name) {
      return this.accounts[name]['total'].toFixed(2)
    },
    // 文字颜色
    textColorWithValue (value) {
      var number = parseFloat(value)
      if (number > 0) {
        return 'rise-text-color'
      } else if (number === 0) {
        return 'normal-text-color'
      } else {
        return 'fall-text-color'
      }
    },
    // 文字颜色
    moneyCategoryTextColor (index) {
      if (index === 0 || index === 1) {
        return 'normal-text-color'
      }
      if (this.marketCapCompareStatus === 1) {
        return 'rise-text-color'
      } else if (this.marketCapCompareStatus === 0) {
        return 'normal-text-color'
      } else {
        return 'fall-text-color'
      }
    },
    category3holdingIndexValue (item) {
      if (item.holding > 0) {
        var rate = item.total / item.holding
        var holdingIndexValue = item.current / (1 + rate)
        if (holdingIndexValue > 0) {
          return holdingIndexValue.toFixed(0)
        } else {
          return 0
        }
      }
      return 0
    },
    category3GainRate (item) {
      if (item.holding > 0) {
        var rate = item.total / item.holding
        return (rate * 100).toFixed(0) + '%'
      }
      return '0%'
    },
    category3GainRateTextColor (item) {
      if (item.holding > 0) {
        var rate = item.total / item.holding
        if (rate > 0) {
          return 'rise-text-color'
        } else if (rate === 0) {
          return 'normal-text-color'
        } else {
          return 'fall-text-color'
        }
      }
      return 'normal-text-color'
    },
    evalRankBackground (percentile) {
      if (percentile === 0.0) {
        return 'background-color:#333'
      }
      var style = ''
      if (percentile <= 0.4) {
        style = 'background: linear-gradient(90deg, #0fae9d ' + percentile * 100 + '%,#333333 ' + (percentile + 0.1) * 100 + '%);'
        return style
      } else if (percentile > 0.4 && percentile <= 0.8) {
        style = 'background: linear-gradient(90deg, #e5a43a ' + percentile * 100 + '%,#333333 ' + (percentile + 0.1) * 100 + '%);'
        return style
      } else if (percentile > 0.8) {
        if (1 - percentile < 0.1) {
          var tailRate = 1 - percentile
          style = 'background: linear-gradient(90deg, #fe5a4b ' + percentile * 100 + '%,#333333 ' + (percentile + tailRate) * 100 + '%);'
        } else {
          style = 'background: linear-gradient(90deg, #fe5a4b ' + percentile * 100 + '%,#333333 ' + (percentile + 0.1) * 100 + '%);'
        }
        return style
      } else {
        return 'background-color: #333'
      }
    },
    // 基金所属不同分类底色，及场内基金名称标红
    categoryColorWithValue (item) {
      var bgClass = 'categorybg'
      switch (item.category1_name) {
        case this.categorys[0]:
          return bgClass + 1
        case this.categorys[1]:
          return bgClass + 2
        case this.categorys[2]:
          return bgClass + 3
        case this.categorys[3]:
          return bgClass + 4
        case this.categorys[4]:
          return bgClass + 5
        case this.categorys[5]:
          return bgClass + 6
        case '冻结资金':
          return bgClass + 7
        case '现金':
          return bgClass + 8
        default:
          return bgClass + 8
      }
    }
  },
  data () {
    return {
      showDaily: true,
      showEval: false,
      moneyCategorys: ['可用现金', '冻结资金', '基金市值', '家庭总计'],
      categorys: ['A 股', '海外新兴', '海外成熟', '混合型', '债券', '商品'],
      accounts: {},
      category3Items: {},
      isUpdating: true,
      marketCapCompareStatus: 0,
      myMoneyInfos: this.moneyinfos,
      myEstimates: this.estimates,
      myHoldings: this.holdings,
      totalDailyGain: 0,
      totalHoldingGain: 0,
      totalMarketCap: 0,
      totalFamilyCap: 0
    }
  },
  created: function () {},
  watch: {
    holdings: {
      handler (newValue, oldValue) {
        this.myHoldings = this.holdings
      },
      immediate: true,
      deep: true
    },
    moneyinfos: {
      handler (newValue, oldValue) {
        this.myMoneyInfos = this.moneyinfos
      },
      immediate: true,
      deep: true
    },
    estimates: {
      handler (newValue, oldValue) {
        this.myEstimates = this.estimates
        this.accounts = {}
        this.totalDailyGain = 0.0
        this.totalHoldingGain = 0.0
        // 暂存一下上次的市值
        var lastMarketCap = this.totalMarketCap
        this.totalMarketCap = 0.0
        // 按 category3 把 myHoldings 分组聚合，来自网络代码（map 是品种个数，dest 是每个三级分类的 group by）
        var map = {}
        var dest = []

        for (var index in this.myHoldings) {
          var fundItem = this.myHoldings[index]
          var code = fundItem.code
          if (Object.keys(this.accounts).indexOf(fundItem.account) === -1) {
            // 唯一账户
            this.accounts[fundItem.account] = { today: 0, total: 0 }
          }
          // 拿估值
          for (var key in this.myEstimates.estimate) {
            if (key === code) {
              var estiItem = this.myEstimates.estimate[key]
              fundItem['market'] = estiItem.market
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] =
                parseFloat(estiItem.gszzl).toFixed(2) + '%'
              // 今天数据
              fundItem['dailyChange'] =
                (parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) *
                fundItem.holding_volume
              this.accounts[fundItem.account]['today'] += parseFloat(
                fundItem.dailyChange
              )
              this.totalDailyGain =
                this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] =
                (
                  (parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) -
                    1) *
                  100
                ).toFixed(2) + '%'
              fundItem['totalChange'] =
                (parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) *
                fundItem.holding_volume
              this.accounts[fundItem.account]['total'] += parseFloat(
                fundItem.totalChange
              )
              this.totalHoldingGain =
                this.totalHoldingGain + parseFloat(fundItem.totalChange)
              // 基金总市值
              fundItem['marketCap'] = parseFloat(estiItem.gsz) * parseFloat(fundItem.holding_volume)
              this.totalMarketCap = this.totalMarketCap + fundItem['marketCap']
              break
            }
          }
          // 失败？
          for (var key2 in this.myEstimates.nav) {
            if (key2 === code) {
              estiItem = this.myEstimates.nav[key2]
              fundItem['market'] = estiItem.market
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] =
                parseFloat(estiItem.gszzl).toFixed(2) + '%'
              // 今天数据
              fundItem['dailyChange'] =
                (parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) *
                fundItem.holding_volume
              this.accounts[fundItem.account]['today'] += parseFloat(
                fundItem.dailyChange
              )
              this.totalDailyGain =
                this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] =
                (
                  (parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) -
                    1) *
                  100
                ).toFixed(2) + '%'
              fundItem['totalChange'] =
                (parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) *
                fundItem.holding_volume
              this.accounts[fundItem.account]['total'] += parseFloat(
                fundItem.totalChange
              )
              this.totalHoldingGain =
                this.totalHoldingGain + parseFloat(fundItem.totalChange)
              // 基金总市值
              fundItem['marketCap'] = parseFloat(estiItem.gsz) * parseFloat(fundItem.holding_volume)
              this.totalMarketCap = this.totalMarketCap + fundItem['marketCap']
              break
            }
          }
          // 按三级分类统计
          if (!map[fundItem.category3]) {
            dest.push({
              name: fundItem.category3,
              data: [fundItem]
            })
            map[fundItem.category3] = 1
          } else {
            for (var j = 0; j < dest.length; j++) {
              var dj = dest[j]
              if (dj.name === fundItem.category3) {
                dj.data.push(fundItem)
                map[fundItem.category3] += 1
                break
              }
            }
          }
        }
        // 三级分类的汇总
        var sum = {}
        for (var i = 0; i < dest.length; i++) {
          var category3 = dest[i]
          var arr = category3.data
          var category3DailyChange = 0.0
          var category3TotalChange = 0.0
          var category3HoldingMoney = 0.0
          var category3MarketCap = 0.0
          for (j = 0; j < arr.length; j++) {
            fundItem = arr[j]
            // console.log(fundItem.code, fundItem.name, fundItem.account, fundItem.totalChange)
            category3DailyChange += fundItem.dailyChange
            category3TotalChange += fundItem.totalChange
            category3HoldingMoney += fundItem.holding_money
            category3MarketCap += fundItem.marketCap
          }
          sum[category3.name] = {
            daily: category3DailyChange,
            total: category3TotalChange,
            holding: category3HoldingMoney,
            marketcap: category3MarketCap
          }
        }
        this.category3Items = sum
        this.totalDailyGain = parseFloat(this.totalDailyGain).toFixed(2)
        this.totalHoldingGain = parseFloat(this.totalHoldingGain).toFixed(2)
        if (lastMarketCap < 1 || lastMarketCap === this.totalMarketCap) {
          // 初始化时，last 值应该是 0，所以显示白色资金数
          this.marketCapCompareStatus = 0
        } else if (lastMarketCap > this.totalMarketCap) {
          this.marketCapCompareStatus = -1
        } else if (lastMarketCap < this.totalMarketCap) {
          this.marketCapCompareStatus = 1
        }
        this.totalMarketCap = parseFloat(this.totalMarketCap).toFixed(2)
        this.isUpdating = true
        // console.log(this.category3Items);
        setTimeout(() => {
          this.isUpdating = false
        }, 1500)
      },
      immediate: true,
      deep: true
    },
    evals: {
      handler (newValue, oldValue) {
        this.evals = newValue
        for (var key1 in this.category3Items) {
          var category3 = this.category3Items[key1]
          // console.log(key1, category3)
          for (var key2 in this.evals) {
            var evalItem = this.evals[key2]
            // console.log(key2, evalItem)
            if (evalItem.category3_name === key1) {
              // console.log(evalItem.category3_name, key1)
              evalItem['daily'] = category3.daily.toFixed(1)
              evalItem['total'] = category3.total.toFixed(1)
              evalItem['holding'] = category3.holding.toFixed(1)
              evalItem['marketcap'] = category3.marketcap.toFixed(1)
              break
            }
          }
        }
        // console.log(this.evals);
      },
      immediate: true,
      deep: true
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

.huatai {
  background-color: #FF7C9E;
}
.huabao {
  background-color: #B0D482;
}
.tiantian {
  background-color: #FF8361;
}
.qieman {
  background-color: #6EB5FF;
}
.danjuan {
  background-color: #F0DC5A;
}
.zhifubao {
  background-color: #DBB6AC;
}
.unknow {
  background-color: #FF0000;
}

.container {
  display: flex;
  flex-wrap:wrap;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.moneyCategoryTitle {
  display: flex;
  justify-content:center;
  align-items: center;
  width: 2.45rem;
  font-size: 0.33rem;
  color: #FFFFFF;
  background-color: #333333;
}

.moneyCategorySum {
  display: flex;
  justify-content:center;
  align-items: center;
  width: 2.45rem;
  font-size: 0.33rem;
  background-color: #333333;
}

.categoryTitle {
  display: flex;
  justify-content:center;
  align-items: center;
  width: 1.6rem;
  font-size: 0.33rem;
  color: #FFFFFF;
  background-color: #333333;
}

.categorySum {
  display: flex;
  justify-content:center;
  align-items: center;
  width: 1.6rem;
  font-size: 0.33rem;
  background-color: #333333;
}

.sumcell {
  display: inline-flex;
  justify-content:center;
  align-items:center;
  flex-direction: column;
  margin:0px 0px;
  width: 100%;
}

.sumcontainer {
  display: flex;
  align-items: center;
  width: 100%;
}

.summaryContainer {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 10rem;
}

.summaryValueContainer {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 5rem;
}

.summaryRateContainer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 5rem;
}

.summaryTitle {
  display: flex;
  align-items: center;
  justify-content: center;
  color:#FFF;
  margin:0.12rem 0.06rem;
  font-size: 0.4rem;
}

.summaryValue {
  display: flex;
  align-items: center;
  justify-content: center;
  margin:0.12rem 0.06rem;
  font-size: 0.4rem;
}

.accountCell {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  width: 2.4rem;
  margin: 1px;
}

.title {
  display: flex;
  justify-content: center;
  align-items: center;
  color: #333;
  font-size: 0.4rem;
}

.today {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.4rem;
}

.total {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.4rem;
}

.flash {
  animation: flash 1.2s;
}

.category3cell {
  display: flex;
  width: 10rem;
  justify-content:flex-start;
  align-items: center;
  background-color: #000000;
}

.category3name {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:center;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 2rem;
  height: 0.5rem;
  font-size: 0.33rem;
  text-align: right;
  color:#FFFFFF;
  background-color: #333333;
}

.category3-narrow-value {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 1.1rem;
  height: 0.5rem;
  font-size: 0.33rem;
  /* text-align: center; */
  color:#FFFFFF;
  background-color: #333333;
  /* 线性背景，覆盖 background-color 属性 */
  /* background: linear-gradient(90deg,#0fae9d 50%,#333333 65%); */
}

.category3-middle-value {
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 1.5rem;
  height: 0.5rem;
  font-size: 0.33rem;
  /* text-align: center; */
  color:#FFFFFF;
  background-color: #333333;
}

.category3-title {
  justify-content:center;
}

/* A 股 */
.categorybg1 {
  background-color: #50C2F9;
}
/* 海外新兴 */
.categorybg2 {
  background-color: #BBEDA8;
}
/* 海外成熟 */
.categorybg3 {
  background-color: #FFC751;
}
/* 混合 */
.categorybg4 {
  background-color: #FF7C9E;
}
/* 债券 */
.categorybg5 {
  background-color: #FF8361;
}
/* 商品 */
.categorybg6 {
  background-color: #DBB6AC;
}
/* 冻结资金 */
.categorybg7 {
  background-color: #DCDCDC;
}
/* 现金 */
.categorybg8 {
  background-color: #F0DC5A;
}

.normal-text-color {
  color: #FFFFFF;
}
.rise-text-color {
  color: #DD2200;
}
.fall-text-color {
  color: #009933;
}

@keyframes flash {
  0% { opacity: 1;}
  25% { opacity: 0;}
  50% { opacity: 1;}
  75% { opacity: 0;}
  100% {opacity: 1;}
}

</style>
