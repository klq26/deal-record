<template>
  <div id="app">
    <FundComponent :holdings="holdings" :estimates="estimates" :countdown="countdown"/>
  </div>
</template>

<script>

import axios from 'axios'
import Vue from 'vue'

import FundComponent from './components/FundComponent'

Vue.prototype.$axios = axios
Vue.config.productionTip = false

var serverIp = 'http://112.125.25.230/'
// serverIp = 'http://127.0.0.1:5000/'

export default {
  name: 'App',
  components: {
    FundComponent
  },
  data () {
    return {
      holdings: [],
      estimates: {},
      countdown: 5 * 60
    }
  },
  methods: {
    familyHolding () {
      var that = this
      axios.get(serverIp + 'familyholding/api/holding?type=1').then(function (response) {
        that.holdings = response.data.data
      })
    },
    familyEstimate () {
      var that = this
      axios.get(serverIp + 'familyholding/api/estimate').then(function (response) {
        that.estimates = response.data.data
      })
    }
  },
  created: function () {
    this.familyHolding()
    var that = this
    // 给首次估值一个 250 毫秒的延迟执行，防止后者先回来，没有更新页面
    setTimeout(() => {
      that.familyEstimate()
    }, 250)
    // 每 5 分钟估值一次
    setInterval(this.familyEstimate, this.countdown * 1000)
  }
}
</script>

<style>
#app {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
