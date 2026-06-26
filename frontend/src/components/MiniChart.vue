<template>
  <div ref="el" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // type: 'pie' | 'gauge'
  type: { type: String, default: 'pie' },
  data: { type: Array, default: () => [] }, // pie: [{name,value}]
  value: { type: Number, default: 0 },       // gauge
  title: { type: String, default: '' },
  height: { type: Number, default: 260 },
})

const el = ref()
let chart = null
const PALETTE = ['#2fe6ff', '#4a8cff', '#19d98a', '#ffb547', '#ff5b6e', '#9d7bff', '#36cfc9']

function optionPie() {
  return {
    color: PALETTE,
    tooltip: { trigger: 'item', backgroundColor: 'rgba(10,20,40,0.92)',
      borderColor: 'rgba(74,140,255,0.3)', textStyle: { color: '#e6f0ff' } },
    legend: { type: 'scroll', orient: 'vertical', right: 8, top: 'center',
      textStyle: { color: '#8da4c8' } },
    series: [{
      type: 'pie', radius: ['42%', '68%'], center: ['38%', '52%'],
      avoidLabelOverlap: true, itemStyle: { borderColor: '#0a1528', borderWidth: 2 },
      label: { show: false }, labelLine: { show: false },
      data: props.data,
    }],
  }
}

function optionGauge() {
  return {
    series: [{
      type: 'gauge', startAngle: 210, endAngle: -30, min: 0, max: 100,
      radius: '92%', center: ['50%', '58%'],
      progress: { show: true, width: 14,
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#19d98a' }, { offset: 1, color: '#2fe6ff' }]) } },
      axisLine: { lineStyle: { width: 14, color: [[1, 'rgba(120,160,220,0.12)']] } },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      pointer: { show: false },
      anchor: { show: false },
      detail: { valueAnimation: true, fontSize: 30, fontWeight: 700,
        color: '#2fe6ff', offsetCenter: [0, 0], formatter: '{value}%' },
      title: { show: !!props.title, offsetCenter: [0, '38%'], color: '#8da4c8', fontSize: 13 },
      data: [{ value: props.value, name: props.title }],
    }],
  }
}

function render() {
  if (!chart) return
  chart.setOption(props.type === 'gauge' ? optionGauge() : optionPie(), true)
}
function resize() { chart && chart.resize() }

onMounted(async () => {
  await nextTick()
  chart = echarts.init(el.value)
  render()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})
watch(() => [props.data, props.value], render, { deep: true })
</script>
