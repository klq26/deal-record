<template>
  <div class="modal-bg" v-show="show">
    <div class="modal-container">
      <div class="modal-header">
        {{ title }}
      </div>
      <div class="modal-main">
        <!-- <slot></slot> -->
        <div class="modal-info" style="display:flex; justify-content:center; width=max-content;">{{message}}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoadingComponent',
  props: {
    show: {
      type: Boolean,
      default: true
    },
    title: {
      type: String,
      default: ''
    },
    popupMessage: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      message: this.popupMessage
    }
  },
  methods: {
  }
}
</script>

<!-- Add 'scoped' attribute to limit CSS to this component only -->
<style scoped>

.modal-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 10rem;
  height: 10rem;
  background: rgba(0,0,0,.5);
  z-index: 10;
}

.modal-container {
  background: #FFFFFF;
  border-radius: 10px;
  overflow: hidden;
  position: fixed;
  top: 30%;
  left: 50%;
  width: 8rem;
  transform: translate(-50%,-50%);
}

.modal-header {
  height: 1rem;
  background: #409EFF;
  color: #333;
  font-size: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: move;
}

.modal-main {
  padding: 20px 0px;
  width: 8rem;
  height: 2rem;
  color: #333;
  font-size: 0.5rem;
}
</style>
