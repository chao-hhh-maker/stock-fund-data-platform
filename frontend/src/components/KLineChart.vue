<template>
  <div ref="el" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // rows: [{trade_date, open, close, low, high, volume, pct_change}]
  rows: { type: Array, default: () => [] },
  height: { type: Number, default: 420 },
})

const el = ref()
let chart = null
const UP = '#f06464'      // A股：涨红
const DOWN = '#20c997'    // A股：跌绿

function render() {
  if (!chart) return
  const dates = props.rows.map((r) => r.trade_date)
  // ECharts K线数据格式：[open, close, low, high]
  const kData = props.rows.map((r) => [r.open, r.close, r.low, r.high])
  const volumes = props.rows.map((r, i) => ({
    value: r.volume,
    itemStyle: { color: r.close >= r.open ? UP + 'aa' : DOWN + 'aa' },
  }))

  chart.setOption({
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(16,20,27,0.96)', borderColor: 'rgba(148,163,184,0.24)',
      textStyle: { color: '#edf2f7' },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: 56, right: 24, top: 20, height: '58%' },
      { left: 56, right: 24, top: '74%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.20)' } },
        axisLabel: { color: '#707b8e' } },
      { type: 'category', gridIndex: 1, data: dates, axisLabel: { show: false },
        axisLine: { lineStyle: { color: 'rgba(148,163,184,0.20)' } } },
    ],
    yAxis: [
      { scale: true, splitLine: { lineStyle: { color: 'rgba(148,163,184,0.10)' } },
        axisLabel: { color: '#707b8e' } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false },
        splitLine: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1] },
      { type: 'slider', xAxisIndex: [0, 1], height: 16, bottom: 8,
        borderColor: 'transparent', fillerColor: 'rgba(53,208,186,0.20)',
        textStyle: { color: '#707b8e' } },
    ],
    series: [
      {
        name: 'K线', type: 'candlestick', data: kData,
        itemStyle: { color: UP, color0: DOWN, borderColor: UP, borderColor0: DOWN },
      },
      { name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes },
    ],
  }, true)
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
watch(() => props.rows, render, { deep: true })
</script>

