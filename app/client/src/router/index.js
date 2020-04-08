import Vue from 'vue'
import Router from 'vue-router'
import FundComponent from '@/components/FundComponent'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'FundComponent',
      component: FundComponent
    }
  ]
})
