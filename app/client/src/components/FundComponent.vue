<template>
  <div class="container">
    <div>{{datetime}}</div>
    <div :class="textColorWithValue(totalDailyGain)">{{totalDailyGain}}</div>
    <div class="cell">
      <p class="fundcode title">代码</p>
      <p class="fundname title">名称</p>
      <p class="fundnav title">成本</p>
      <p class="fundnav title">估值</p>
      <p class="dailyChangeRate title">涨跌</p>
      <p class="dailyChange title">盈亏</p>
    </div>
    <div class="cell border" v-for="item in holdings" :key="item.index">
      <p class="fundcode" :class="categoryColorWithValue(item)">{{item.code}}</p>
      <p class="fundname" :class="categoryColorWithValue(item)">{{item.name}}</p>
      <p class="fundnav">{{item.holding_nav}}</p>
      <p class="fundnav">{{item.estimate_nav}}</p>
      <p class="dailyChangeRate" :class="textColorWithValue(item.estimate_rate)">{{item.estimate_rate}}</p>
      <p class="dailyChange" :class="textColorWithValue(item.dailyChange)">{{item.dailyChange}}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FundComponent',
  props: {
    holdings: {
      type: Array,
      default () {
        return []
      }
    },
    estimates: {},
    datetime: 'time',
    totalDailyGain: 0
  },
  methods: {
    updateTime () {
      var date = new Date()
      var year = date.getFullYear()
      var month = this.prefixInteger(date.getMonth() + 1, 2)
      var day = this.prefixInteger(date.getDate(), 2)
      var hh = this.prefixInteger(date.getHours(), 2)
      var mi = this.prefixInteger(date.getMinutes(), 2)
      var ss = this.prefixInteger(date.getSeconds(), 2)
      var dayTag = '日一二三四五六'.charAt(date.getDay())
      var wk = '周' + dayTag
      this.datetime = year + '-' + month + '-' + day + ' ' + hh + ':' + mi + ':' + ss + ' '
    },
    // 时间前置补 0
    prefixInteger (num, length) {
      return (Array(length).join('0') + num).slice(-length)
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
    // 基金所属不同分类底色，及场内基金名称标红
    categoryColorWithValue(item) {
      var bgClass = "categorybg"
      if (item.market === '场内') {
        bgClass = "innerFundText " + "categorybg"
      }
      switch(item.category1) {
        case "A 股":
          return bgClass + 1
        case "海外新兴":
          return bgClass + 2
        case "海外成熟":
          return bgClass + 3
        case "混合":
          return bgClass + 4
        case "债券":
          return bgClass + 5
        case "商品":
          return bgClass + 6
        case "冻结资金":
          return bgClass + 7
        case "现金":
          return bgClass + 8
        default:
          return bgClass + 8
      }
    }
  },
  data () {
    return {
      msg: 'Welcome to Your Vue.js App'
    }
  },
  created: function () {
    this.updateTime()
    setInterval(this.updateTime, 1 * 1000)
  },
  watch: {
    estimates: {
      handler (newValue, oldValue) {
        if (typeof (newValue) === 'undefined') {
          return
        }
        this.totalDailyGain = 0.0
        for (var index in this.holdings) {
          var fundItem = this.holdings[index]
          var code = fundItem.code
          // 拿估值
          for (var key in this.estimates.success) {
            if (key === code) {
              var estiItem = this.estimates.success[key]
              fundItem['estimate_nav'] = estiItem.gsz
              fundItem['estimate_rate'] = parseFloat(estiItem.gszzl).toFixed(2) + '%'
              fundItem['dailyChange'] = ((parseFloat(estiItem.gsz) - parseFloat(estiItem.dwjz)) * fundItem.holding_volume).toFixed(2)
              fundItem['market'] = estiItem.market
              this.totalDailyGain = this.totalDailyGain + parseFloat(fundItem.dailyChange)
              break
            }
          }
          // 失败？
          for (var key in this.estimates.failure) {
            if (key === code) {
              var estiItem = this.estimates.success[key]
              fundItem['estimate_nav'] = '暂无'
              fundItem['estimate_rate'] = '0.00%'
              fundItem['dailyChange'] = parseFloat(0.00).toFixed(2)
              break
            }
          }
        }
        // 格式化
        this.totalDailyGain = parseFloat(this.totalDailyGain).toFixed(2)
        
        // this.isUpdating = true
        // setTimeout(() => {
        //   this.isUpdating = false
        // }, 1500)
        this.updateTime()
      },
      immediate: true,
      deep: true
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

.normal-text-color {
  color: #F0F0F0;
}
.rise-text-color {
  color: #DD2200;
}
.fall-text-color {
  color: #009933;
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

.cell {
  display: inline-flex;
  background-color: #000000;
}

.container {
  display: inline-flex;
  flex-direction: column;
  background-color: #DDDDD0;
}

.fundcode {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 58px;
  height: 25px;
  font-size: 16px;
}

.fundname {
  /* 解决纯数字时偏上的问题 */
  display: flex;
  align-items: center;
  margin: 1px;
  padding: 1px;
  width: 116px;
  height: 25px;
  font-size: 16px;
  text-align: left;
}

.fundnav {
    /* 解决纯数字时偏上的问题 */
  display: flex;
  justify-content:flex-end;
  align-items: center;
  margin: 1px;
  padding: 1px 2px;
  width: 50px;
  height: 25px;
  font-size: 16px;
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
  padding: 1px 2px;
  width: 50px;
  height: 25px;
  font-size: 16px;
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
  width: 70px;
  height: 25px;
  font-size: 16px;
  text-align: right;
  background-color: #333333;
}

/* CSS 声明顺序很关键。后面声明的会覆盖前面声明的，不管你再 class 赋值处的先后顺序如何 */
.title {
  justify-content:center;
  align-items: center;
  text-align: center;
  color: #FFFFFF;
  background-color: #333333;
}

/* 场内基金提高辨识度 */
.innerFundText {
  color: #CC0000;
}

</style>
