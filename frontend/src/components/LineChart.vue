<template>
  <div ref="el" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  height: { type: Number, default: 360 },
  area: { type: Boolean, default: true },
})

const el = ref()
let chart = null
const PALETTE = ['#35d0ba', '#7aa2f7', '#f2b84b', '#f06464', '#20c997']

function gradient(color) {
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: color + '55' },
    { offset: 1, color: color + '02' },
  ])
}

function render() {
  if (!chart) return
  chart.setOption({
    color: PALETTE,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(16,20,27,0.96)',
      borderColor: 'rgba(148,163,184,0.24)',
      textStyle: { color: '#edf2f7' },
    },
    legend: {
      data: props.series.map((s) => s.name),
      textStyle: { color: '#a7b0c0' },
      top: 4,
    },
    grid: { left: 54, right: 24, top: 40, bottom: 54 },
    xAxis: {
      type: 'category', data: props.categories, boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(148,163,184,0.20)' } },
      axisLabel: { color: '#707b8e' },
    },
    yAxis: {
      type: 'value', scale: true,
      splitLine: { lineStyle: { color: 'rgba(148,163,184,0.10)' } },
      axisLabel: { color: '#707b8e' },
    },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 16, bottom: 12, borderColor: 'transparent',
        fillerColor: 'rgba(53,208,186,0.20)', textStyle: { color: '#707b8e' } },
    ],
    series: props.series.map((s, i) => ({
      name: s.name, type: 'line', smooth: true, showSymbol: false,
      lineStyle: { width: 2 },
      areaStyle: props.area ? { color: gradient(PALETTE[i % PALETTE.length]) } : undefined,
      data: s.data,
    })),
  }, true)
}

function resize() { chart && chart.resize() }

onMounted(async () => {
  await nextTick()
  chart = echarts.init(el.value, null, { renderer: 'canvas' })
  render()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
})
watch(() => [props.categories, props.series], render, { deep: true })
</script>

