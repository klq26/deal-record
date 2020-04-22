<template>
  <div id="app">
  <LoadingComponent :show="showLoading" title="加载中" popupMessage="接口查询中，请稍后"/>
  <ul>
    <li v-for="(tab, index) in tabs" @click="toggle(index)" :class="{active: active == index}" :key=index>
      {{tab.type}}
    </li>
  </ul>
  <div style="display:flex;width:100%;width:10rem;">
    <!-- 时间 -->
    <div style="display:flex; align-items: center; justify-content: flex-start; color:#FFF; margin:4px 0.06rem; width:50%;font-size: 0.4rem;" @click.stop="datetimeClicked()">{{datetime}}</div>
    <!-- 倒计时 -->
    <div style="display:flex; justify-content:flex-end; color:#FFF; margin:4px 0.06rem; width:50%;font-size: 0.4rem;">距下次更新约 {{myCountdown}} 秒</div>
  </div>
  <AccountSummaryComponent :holdings="accountholdings" :estimates="estimates" v-show="active == 0"/>
  <FundComponent :holdings="fundholdings" :estimates="estimates" v-show="active == 1"/>
  <FundDetailComponent :holdings="fundholdings" :estimates="estimates" v-show="active == 2"/>
  </div>
</template>

<script>

import axios from 'axios'
import Vue from 'vue'

import FundComponent from './components/FundComponent'
import FundDetailComponent from './components/FundDetailComponent'
import AccountSummaryComponent from './components/AccountSummaryComponent'
import LoadingComponent from './components/LoadingComponent'

Vue.prototype.$axios = axios
Vue.config.productionTip = false

// 根据不同环境，动态切换 API 域名
var serverIp = process.env.API_ROOT

export default {
  name: 'App',
  components: {
    FundComponent,
    FundDetailComponent,
    AccountSummaryComponent,
    LoadingComponent
  },
  data () {
    return {
      showLoading: true,
      myCountdown: 5 * 60,
      fundholdings: [],
      accountholdings: [],
      estimates: {},
      showDetail: false,
      active: 0,
      tabs: [
        {
          type: '分账户明细'
        },
        {
          type: '持仓估值'
        },
        {
          type: '持仓详情'
        }
      ]
    }
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
      this.datetime = year + '-' + month + '-' + day + ' ' + hh + ':' + mi + ':' + ss + ' '
      if (this.myCountdown > 0) {
        this.myCountdown = this.myCountdown - 1
      }
    },
    // 时间前置补 0
    prefixInteger (num, length) {
      return (Array(length).join('0') + num).slice(-length)
    },
    toggle (i) {
      this.active = i
    },
    fundHolding () {
      var that = this
      this.showLoading = true
      axios.get(serverIp + 'familyholding/api/fundholding').then(function (response) {
        that.fundholdings = response.data.data
      })
    },
    accountHolding () {
      var that = this
      this.showLoading = true
      axios.get(serverIp + 'familyholding/api/accountholding').then(function (response) {
        that.accountholdings = response.data.data
      })
    },
    familyEstimate () {
      var that = this
      this.showLoading = true
      axios.get(serverIp + 'familyholding/api/estimate').then(function (response) {
        that.estimates = response.data.data
        that.myCountdown = 5 * 60
        that.showLoading = false
      })
    }
  },
  created: function () {
    var that = this
    document.onkeyup = function (e) {
      // console.log(e.keyCode)
      var val = that.active
      // 事件对象兼容
      let e1 = e || event || window.event
      // 键盘按键判断:左箭头-37;上箭头-38；右箭头-39;下箭头-40
      if (e1 && e1.keyCode === 37) {
        // console.log('左')
        if (val > 0) {
          val -= 1
        } else {
          val = 2
        }
        that.toggle(val)
      } else if (e1 && e1.keyCode === 38) {
        // console.log('上')
      } else if (e1 && e1.keyCode === 39) {
        // console.log('右')
        if (val < 2) {
          val += 1
        } else {
          val = 0
        }
        that.toggle(val)
      } else if (e1 && e1.keyCode === 40) {
        // console.log('下')
      }
    }
    this.updateTime()
    setInterval(this.updateTime, 1 * 1000)
    this.accountHolding()
    this.fundHolding()
    // 给首次估值一个 500 毫秒的延迟执行，防止后者先回来，没有更新页面
    setTimeout(() => {
      that.familyEstimate()
    }, 500)
    // 每 5 分钟估值一次
    setInterval(this.familyEstimate, this.myCountdown * 1000)
  }
}
</script>

<style>
#app {
  width: 10rem;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

ul{
  width:10rem;
  display:flex;
}

ul li{
  width:3.3333rem;
  height:1rem;
  background: #F0F0F0;
  display: inline-flex;
  border-right:1px solid #333333;
  justify-content: center;
  align-items: center;
  cursor:pointer;
  font-size: 0.4rem;
}

ul li.active{
  background-color: rgb(51,153,254);
  font-weight: bold;
}
</style>
