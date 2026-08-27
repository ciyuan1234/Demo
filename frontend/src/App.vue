<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { api, type Alarm, type Device, type Oxygen, type WaterQuality } from './api'

const ponds = ['POND_001', 'POND_002', 'POND_003']
const pondId = ref(ponds[0])
const device = ref<Device | null>(null)
const latest = ref<WaterQuality | null>(null)
const history = ref<WaterQuality[]>([])
const alarms = ref<Alarm[]>([])
const oxygen = ref<Oxygen | null>(null)
const offline = ref(false)
const chart = ref<HTMLElement>()
let chartInstance: echarts.ECharts | undefined
let timer: number | undefined

const risk = computed(() => latest.value ? (latest.value.do < 3 ? '严重' : latest.value.do < 4 ? '预警' : '正常') : '暂无数据')
const riskType = computed(() => risk.value === '严重' ? 'danger' : risk.value === '预警' ? 'warning' : 'success')

async function load() {
  try {
    const devices = await api.devices()
    device.value = devices.find(item => item.pond_id === pondId.value) ?? devices[0] ?? null
    const selectedPond = device.value?.pond_id ?? pondId.value
    ;[latest.value, history.value, alarms.value] = await Promise.all([
      api.latest(selectedPond), api.history(selectedPond), api.alarms(selectedPond),
    ])
    oxygen.value = await api.oxygen().catch(() => null)
    offline.value = false
    await nextTick()
    renderChart()
  } catch {
    offline.value = true
  }
}

function renderChart() {
  if (!chart.value) return
  chartInstance ??= echarts.init(chart.value)
  const rows = [...history.value].reverse()
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['DO', '温度', 'pH', '浊度'] },
    grid: { left: 45, right: 20, bottom: 35, top: 35 },
    xAxis: { type: 'category', data: rows.map(row => new Date(row.timestamp * 1000).toLocaleTimeString()) },
    yAxis: [{ type: 'value', name: 'DO / 温度' }, { type: 'value', name: 'pH / 浊度' }],
    series: [
      { name: 'DO', type: 'line', smooth: true, data: rows.map(row => row.do) },
      { name: '温度', type: 'line', smooth: true, data: rows.map(row => row.temperature) },
      { name: 'pH', type: 'line', yAxisIndex: 1, smooth: true, data: rows.map(row => row.ph) },
      { name: '浊度', type: 'line', yAxisIndex: 1, smooth: true, data: rows.map(row => row.turbidity) },
    ],
  })
}

async function command(action: 'start' | 'stop') {
  try { oxygen.value = await api.oxygenCommand(action); ElMessage.success(`已发送${action === 'start' ? '启动' : '停止'}命令`) }
  catch { ElMessage.error('命令发送失败，后端可能未连接') }
}

async function setMode(mode: 'AUTO' | 'MANUAL') {
  try { oxygen.value = await api.oxygenMode(mode) } catch { ElMessage.error('模式切换失败') }
}

function onModeChange(value: string | number | boolean) {
  if (value === 'AUTO' || value === 'MANUAL') setMode(value)
}

watch(pondId, load)
onMounted(() => { load(); timer = window.setInterval(load, 10000) })
onUnmounted(() => { if (timer) window.clearInterval(timer); chartInstance?.dispose() })
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <div><p class="eyebrow">AIoT AQUACULTURE</p><h1>智慧水产养殖平台</h1></div>
      <div class="toolbar"><el-select v-model="pondId" style="width: 150px"><el-option v-for="pond in ponds" :key="pond" :label="pond" :value="pond" /></el-select><el-tag :type="offline ? 'danger' : 'success'">{{ offline ? '后端离线' : '系统在线' }}</el-tag></div>
    </header>
    <el-alert v-if="offline" title="暂时无法连接后端 API，页面不会伪造水质数据。" type="warning" show-icon :closable="false" />
    <section class="cards">
      <el-card v-for="item in [{label:'溶解氧 DO',value: latest ? `${latest.do.toFixed(2)} mg/L` : '--', key:'do'}, {label:'温度',value: latest ? `${latest.temperature.toFixed(1)} °C` : '--', key:'temperature'}, {label:'pH',value: latest ? latest.ph.toFixed(2) : '--', key:'ph'}, {label:'浊度',value: latest ? `${latest.turbidity.toFixed(1)} NTU` : '--', key:'turbidity'}]" :key="item.key" class="metric-card"><span>{{ item.label }}</span><strong>{{ item.value }}</strong></el-card>
    </section>
    <section class="grid">
      <el-card class="chart-card"><template #header><div class="card-title"><span>水质趋势</span><small>{{ latest?.data_source ?? 'no data' }} · {{ latest?.mode ?? '---' }}</small></div></template><div ref="chart" class="chart"></div></el-card>
      <el-card><template #header><div class="card-title"><span>风险与设备</span><el-tag :type="riskType">{{ risk }}</el-tag></div></template><div class="risk-panel"><div class="risk-number">{{ latest ? latest.do.toFixed(1) : '--' }}<small> mg/L DO</small></div><p>{{ risk === '严重' ? '建议立即启动增氧设备' : risk === '预警' ? '请关注 DO 下降趋势' : '当前水质处于监测范围内' }}</p><div class="device-row"><span>设备状态</span><el-tag :type="device?.status === 'ONLINE' ? 'success' : 'info'">{{ device?.status ?? 'UNKNOWN' }}</el-tag></div><div class="device-row"><span>增氧机</span><el-tag :type="oxygen?.status === 'ON' ? 'success' : 'info'">{{ oxygen?.status ?? 'UNKNOWN' }}</el-tag></div><div class="actions"><el-button type="success" @click="command('start')">启动增氧</el-button><el-button @click="command('stop')">停止增氧</el-button></div><el-radio-group :model-value="oxygen?.mode" @change="onModeChange"><el-radio-button label="AUTO">自动模式</el-radio-button><el-radio-button label="MANUAL">手动模式</el-radio-button></el-radio-group></div></el-card>
    </section>
    <el-card><template #header><div class="card-title"><span>最近报警</span><small>{{ alarms.length }} 条</small></div></template><el-table :data="alarms" empty-text="暂无报警"><el-table-column prop="created_at" label="时间" width="190" /><el-table-column prop="level" label="级别" width="110"><template #default="scope"><el-tag :type="scope.row.level === 'CRITICAL' ? 'danger' : 'warning'">{{ scope.row.level }}</el-tag></template></el-table-column><el-table-column prop="message" label="内容" /><el-table-column prop="acknowledged" label="状态"><template #default="scope">{{ scope.row.acknowledged ? '已确认' : '未确认' }}</template></el-table-column></el-table></el-card>
  </main>
</template>
