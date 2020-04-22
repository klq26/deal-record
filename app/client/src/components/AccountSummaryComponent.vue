<template>
  <div class="container" @click="showDaily = !showDaily">
    <!-- 整体情况 -->
    <div class="summaryContainer">
      <div class="summaryTitle" v-show="showDaily">日收益</div>
      <div class="summaryValue" :class="textColorWithValue(totalDailyGain)" v-show="showDaily">{{totalDailyGain}}</div>
      <div class="summaryTitle" v-show="!showDaily">总收益</div>
      <div class="summaryValue" :class="textColorWithValue(totalHoldingGain)" v-show="!showDaily">{{totalHoldingGain}}</div>
    </div>
    <!-- 分类汇总 -->
    <div class="sumcontainer">
      <div class="sumcell" v-for="item in categorys" :key="item.index">
        <div class="categoryTitle">{{item}}</div>
        <div class="categorySum" :class="textColorWithValue(sum(item))">{{sum(item)}}</div>
      </div>
    </div>
    <!-- 账户收益 -->
    <div class="accountCell" :class="accountBackground(item)" v-for="item in Object.keys(accounts)" :key="item.index">
      <div class="title">{{item}}</div>
      <div class="today" :class="[textColorWithValue(today(item)), {flash : isUpdating}]">{{today(item)}}</div>
      <div class="total" :class="[textColorWithValue(total(item)), {flash : isUpdating}]">{{total(item)}}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AccountSummaryComponent',
  props: [
    'holdings',
    'estimates'
  ],
  methods: {
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
      } else if (name.indexOf('螺丝钉') !== -1 || name.indexOf('钉钉宝') !== -1) {
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
    }
  },
  data () {
    return {
      showDaily: true,
      categorys: [
        'A 股',
        '海外新兴',
        '海外成熟',
        '混合型',
        '债券',
        '商品'
      ],
      accounts: {},
      isUpdating: true,
      myEstimates: this.estimates,
      myHoldings: this.holdings,
      totalDailyGain: 0,
      totalHoldingGain: 0
    }
  },
  created: function () {
  },
  watch: {
    holdings: {
      handler (newValue, oldValue) {
        this.myHoldings = this.holdings
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
        for (var index in this.myHoldings) {
          var fundItem = this.myHoldings[index]
          var code = fundItem.code
          if (Object.keys(this.accounts).indexOf(fundItem.account) === -1) {
            // 唯一账户
            this.accounts[fundItem.account] = {'today': 0, 'total': 0}
          }
          // 拿估值
          for (var key in this.myEstimates.estimate) {
            if (key === code) {
              var estiItem = this.myEstimates.estimate[key]
              fundItem['market'] = estiItem.market
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] = parseFloat(estiItem.gszzl).toFixed(2) + '%'
              // 今天数据
              fundItem['dailyChange'] = ((parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) * fundItem.holding_volume)
              this.accounts[fundItem.account]['today'] += parseFloat(fundItem.dailyChange)
              this.totalDailyGain = this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] = ((parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) - 1) * 100).toFixed(2) + '%'
              fundItem['totalChange'] = ((parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) * fundItem.holding_volume)
              this.accounts[fundItem.account]['total'] += parseFloat(fundItem.totalChange)
              this.totalHoldingGain = this.totalHoldingGain + parseFloat(fundItem.totalChange)
              break
            }
          }
          // 失败？
          for (var key2 in this.myEstimates.nav) {
            if (key2 === code) {
              estiItem = this.myEstimates.nav[key2]
              fundItem['market'] = estiItem.market
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] = parseFloat(estiItem.gszzl).toFixed(2) + '%'
              // 今天数据
              fundItem['dailyChange'] = ((parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) * fundItem.holding_volume)
              this.accounts[fundItem.account]['today'] += parseFloat(fundItem.dailyChange)
              this.totalDailyGain = this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] = ((parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) - 1) * 100).toFixed(2) + '%'
              fundItem['totalChange'] = ((parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) * fundItem.holding_volume)
              this.accounts[fundItem.account]['total'] += parseFloat(fundItem.totalChange)
              this.totalHoldingGain = this.totalHoldingGain + parseFloat(fundItem.totalChange)
              break
            }
          }
        }
        this.totalDailyGain = parseFloat(this.totalDailyGain).toFixed(2)
        this.totalHoldingGain = parseFloat(this.totalHoldingGain).toFixed(2)
        this.isUpdating = true
        setTimeout(() => {
          this.isUpdating = false
        }, 1500)
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
.normal-text-color {
  color: #333333;
}
.rise-text-color {
  color: #DD2200;
}
.fall-text-color {
  color: #009933;
}

.container {
  display: flex;
  flex-wrap:wrap;
  justify-content: center;
  width: 100%;
  height: 100%;
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

@keyframes flash {
  0% { opacity: 1;}
  25% { opacity: 0;}
  50% { opacity: 1;}
  75% { opacity: 0;}
  100% {opacity: 1;}
}

</style>
