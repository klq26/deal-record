<template>
  <div class="container">
    <!-- 整体情况 -->
    <div class="summaryContainer">
      <div style="color:#FFF;margin:4px 0.06rem;display:inline-block;font-size: 0.33rem;">日收益</div>
      <div style="margin:4px 0.06rem;display:inline-block;font-size: 0.33rem;" :class="textColorWithValue(totalDailyGain)">{{totalDailyGain}}</div>
    </div>
    <div class="summaryContainer">
      <div style="color:#FFF;margin:4px 0.06rem;display:inline-block;font-size: 0.33rem;">总收益</div>
      <div style="margin:4px 0.06rem;display:inline-block;font-size: 0.33rem;" :class="textColorWithValue(totalHoldingGain)">{{totalHoldingGain}}</div>
    </div>
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
        console.log(this.myHoldings.length)
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

.summaryContainer {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  width: 10rem;
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
  font-size: 0.33rem;
}

.today {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.33rem;
}

.total {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.33rem;
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
