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
    <!-- 基金详情 -->
    <div class="fundcell">
      <p class="fundcode title">代码</p>
      <p class="fundname title">名称</p>
      <p class="fundnav title">成本</p>
      <p class="fundnav title">估值</p>
      <p class="dailyChangeRate title" v-show="showDaily">日涨跌</p>
      <p class="dailyChange title" v-show="showDaily">日盈亏</p>
      <p class="dailyChangeRate title" v-show="!showDaily">总涨跌</p>
      <p class="dailyChange title" v-show="!showDaily">总盈亏</p>
    </div>
    <div class="fundcell" v-for="item in myHoldings" :key="item.index">
      <p class="fundcode" :class="[categoryColorWithValue(item), marketColor(item)]">{{item.code}}</p>
      <p class="fundname" :class="[categoryColorWithValue(item), marketColor(item)]">{{item.name}}</p>
      <p class="fundnav" :class="navColorWithValue(item)" >{{item.holding_nav}}</p>
      <div class="fundcell" :class="{flash : isUpdating}">
      <p class="fundnav">{{item.estimate_nav}}</p>
      <p class="dailyChangeRate" :class="textColorWithValue(item.estimate_rate)" v-show="showDaily">{{item.estimate_rate}}</p>
      <p class="dailyChange" :class="textColorWithValue(item.dailyChange)" v-show="showDaily">{{item.dailyChange}}</p>
      <p class="dailyChangeRate" :class="textColorWithValue(item.total_estimate_rate)" v-show="!showDaily">{{item.total_estimate_rate}}</p>
      <p class="dailyChange" :class="textColorWithValue(item.totalChange)" v-show="!showDaily">{{item.totalChange}}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FundComponent',
  props: [
    'holdings',
    'estimates'
  ],
  methods: {
    marketColor (item) {
      if (item.market === '场外') {
        return ''
      } else {
        return 'inner-fund-text-color'
      }
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
    navColorWithValue (item) {
      var estiNav = parseFloat(item.estimate_nav)
      var holdingNav = parseFloat(item['holding_nav'])
      if (holdingNav < estiNav) {
        return 'rise-text-color'
      } else if (holdingNav === estiNav) {
        return 'normal-text-color'
      } else {
        return 'fall-text-color'
      }
    },
    // 基金所属不同分类底色，及场内基金名称标红
    categoryColorWithValue (item) {
      var bgClass = 'categorybg'
      if (item.market === '场内') {
        bgClass = 'innerFundText ' + 'categorybg'
      }
      switch (item.category1) {
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
    }
  },
  data () {
    return {
      categorys: [
        'A 股',
        '海外新兴',
        '海外成熟',
        '混合型',
        '债券',
        '商品'
      ],
      showDaily: true,
      datetime: 'time',
      totalDailyGain: 0,
      totalHoldingGain: 0,
      isUpdating: true,
      myEstimates: this.estimates,
      myHoldings: this.holdings
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
        if (typeof (newValue) === 'undefined') {
          return
        }
        this.myEstimates = newValue
        this.totalDailyGain = 0.0
        this.totalHoldingGain = 0.0
        for (var index in this.myHoldings) {
          var fundItem = this.myHoldings[index]
          var code = fundItem.code
          // 拿估值
          for (var key in this.myEstimates.estimate) {
            if (key === code) {
              var estiItem = this.myEstimates.estimate[key]
              fundItem['market'] = estiItem.market
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] = parseFloat(estiItem.gszzl).toFixed(2) + '%'
              // 今天数据
              fundItem['dailyChange'] = ((parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) * fundItem.holding_volume).toFixed(2)
              this.totalDailyGain = this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] = ((parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) - 1) * 100).toFixed(2) + '%'
              fundItem['totalChange'] = ((parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) * fundItem.holding_volume).toFixed(2)
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
              fundItem['dailyChange'] = ((parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) * fundItem.holding_volume).toFixed(2)
              this.totalDailyGain = this.totalDailyGain + parseFloat(fundItem.dailyChange)
              // 整体数据
              fundItem['total_estimate_rate'] = ((parseFloat(estiItem.gsz) / parseFloat(fundItem.holding_nav) - 1) * 100).toFixed(2) + '%'
              fundItem['totalChange'] = ((parseFloat(estiItem.gsz) - parseFloat(fundItem.holding_nav)) * fundItem.holding_volume).toFixed(2)
              this.totalHoldingGain = this.totalHoldingGain + parseFloat(fundItem.totalChange)
              break
            }
          }
        }
        // 格式化
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

.fundcell {
  display: flex;
  justify-content:space-between;
  align-items: center;
  background-color: #000000;
}

.container {
  width: 10rem;
  display: inline-flex;
  flex-direction: column;
  background-color: #000000;
}

.fundcode {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 1px;
  padding: 1px;
  min-width: 1.3rem;
  height: 0.5rem;
  font-size: 0.33rem;
}

.fundname {
  /* 解决纯数字时偏上的问题 */
  display: flex;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 2.8rem;
  height: 0.5rem;
  font-size: 0.33rem;
  text-align: left;
}

.fundnav {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 1.2rem;
  height: 0.5rem;
  font-size: 0.33rem;
  text-align: right;
  color:#FFFFFF;
  background-color: #333333;
}

.dailyChangeRate {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px;
  min-width: 1.4rem;
  height: 0.5rem;
  font-size: 0.33rem;
  text-align: right;
  background-color: #333333;
}

.dailyChange {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px;
  min-width: 1.7rem;
  height: 0.5rem;
  font-size: 0.33rem;
  text-align: right;
  background-color: #333333;
}

.normal-text-color {
  color: #F0F0F0;
}
.rise-text-color {
  color: #DD2200;
}
.fall-text-color {
  color: #009933;
}

/* CSS 声明顺序很关键。后面声明的会覆盖前面声明的，不管你再 class 赋值处的先后顺序如何 */
.title {
  justify-content:center;
  align-items: center;
  color: #FFFFFF;
  background-color: #333333;
}

/* 场内基金提高辨识度 */
.inner-fund-text-color {
  color: #CC0000;
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
