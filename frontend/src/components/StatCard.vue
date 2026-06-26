<template>
  <div class="stat-card" :style="{ '--c': color }">
    <div class="stat-top">
      <span class="stat-label">{{ label }}</span>
      <div class="stat-icon-box" v-if="icon">
        <el-icon class="stat-icon"><component :is="icon" /></el-icon>
      </div>
    </div>
    <div class="stat-value mono-num">{{ display }}</div>
    <div class="stat-foot" v-if="sub">
      <span class="trend-dot"></span>{{ sub }}
    </div>
    <div class="stat-bar"><span :style="{ width: normalizedBarWidth }"></span></div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  label: String,
  value: { type: Number, default: 0 },
  color: { type: String, default: '#35d0ba' },
  icon: { type: [Object, Function], default: null },
  sub: { type: String, default: '' },
  suffix: { type: String, default: '' },
  barWidth: { type: String, default: '70%' },
})

const display = ref('0')
const normalizedBarWidth = computed(() => props.barWidth || '70%')

function animate(to) {
  const target = Number(to) || 0
  const dur = 760
  const start = performance.now()
  function step(t) {
    const p = Math.min((t - start) / dur, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    const cur = Math.round(target * eased)
    display.value = cur.toLocaleString() + props.suffix
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

onMounted(() => animate(props.value))
watch(() => props.value, (v) => animate(v))
</script>

<style scoped>
.stat-card {
  position: relative;
  min-height: 146px;
  padding: 18px 18px 16px;
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018));
  border: 1px solid var(--border-soft);
  overflow: hidden;
  transition: border-color 0.18s ease, background 0.18s ease;
}
.stat-card:hover { border-color: color-mix(in srgb, var(--c) 42%, var(--border-strong)); background: rgba(255,255,255,0.045); }
.stat-card::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--c);
}
.stat-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.stat-label { color: var(--text-sub); font-size: 13px; line-height: 1.4; }
.stat-icon-box {
  width: 34px; height: 34px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--c) 15%, transparent);
  color: var(--c);
}
.stat-icon { font-size: 18px; }
.stat-value { font-size: 31px; font-weight: 760; margin: 14px 0 8px; line-height: 1; color: var(--text-main); }
.stat-foot { font-size: 12px; color: var(--text-dim); display: flex; align-items: center; gap: 7px; }
.trend-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--c); }
.stat-bar { margin-top: 14px; height: 4px; border-radius: 999px; background: rgba(255,255,255,0.06); overflow: hidden; }
.stat-bar span { display: block; height: 100%; border-radius: 999px; background: var(--c); transition: width 0.8s ease; }
</style>
