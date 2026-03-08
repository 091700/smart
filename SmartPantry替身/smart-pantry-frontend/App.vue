<template>
  <div class="cyber-dashboard">
    <div class="ambient-light light-1"></div>
    <div class="ambient-light light-2"></div>

    <el-container class="glass-container">
      <el-header height="80px" class="glass-header">
        <div class="logo">🍱 SmartPantry 2.0 <span class="badge">NEXUS</span></div>
        <div class="subtitle">高维 AI 驱动 · 动态生命周期与味觉推演中枢</div>
      </el-header>

      <el-main>
        <el-row :gutter="30">
          <el-col :span="15">
            <div class="glass-card fridge-panel">
              <div class="card-title">
                <span>❄️ 核心保鲜舱 (AI-1 监控中)</span>
                <el-button type="primary" class="cyber-btn" @click="addFormVisible = true">
                  <el-icon><Plus /></el-icon> 录入 / 识别新食材
                </el-button>
              </div>
              
              <el-empty v-if="fridgeItems.length === 0" description="保鲜舱空载..." :image-size="100" />

              <el-row :gutter="15" v-else>
                <el-col :span="8" v-for="item in fridgeItems" :key="item.id" style="margin-bottom: 20px;">
                  <div :class="['glass-item-card', getFreshnessLevel(item.predictedExpireDate)]">
                    <div class="ing-title">{{ getDictName(item.ingredientId) }}</div>
                    <div class="ing-date">入库: {{ item.entryDate }}</div>
                    <div class="ing-date ai-predict">
                      AI 预测变质: <span>{{ item.predictedExpireDate }}</span>
                    </div>
                    <div class="ing-countdown">
                      {{ getDaysLeftText(item.predictedExpireDate) }}
                    </div>
                    <div class="action-bar">
                      <el-button size="small" type="success" plain @click="consumeItem(item.id)">吃掉</el-button>
                      <el-button size="small" type="danger" plain @click="discardItem(item.id)">丢弃</el-button>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-col>

          <el-col :span="9">
            <div class="glass-card magic-panel">
              <div class="card-title">🔮 高维味觉实验室 (AI-2)</div>
              <div class="magic-desc">
                已解除 3 种食材搭配限制。选择任意组合，AI 将在多维张量空间中推演味觉和谐度。
              </div>
              
              <el-select 
                v-model="recipeSelection" 
                multiple 
                placeholder="选择任意数量食材..." 
                class="cyber-select"
                popper-class="cyber-popper">
                <el-option v-for="dict in dictItems" :key="dict.id" :label="dict.name" :value="dict.id" />
              </el-select>
              
              <el-button class="cyber-btn warning-btn" @click="checkRecipe" :loading="checking">
                <el-icon><MagicStick /></el-icon> 启动张量推演
              </el-button>

              <div v-if="harmonyResultVisible" class="result-box">
                <div class="score-display" :style="{ color: harmonyColor }">
                  {{ harmonyScore }}<span class="score-unit">分</span>
                </div>
                <div class="harmony-text" :style="{ color: harmonyColor }">{{ harmonyText }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <div class="mascot-container" @click="pokeMascot">
      <img v-if="mascotState === 'idle'" src="/nailong.png" class="mascot idle-anim" alt="奶龙待机" />
      <video v-else-if="mascotState === 'happy'" src="/nailongdaxiao.webm" class="mascot" autoplay loop muted></video>
      <video v-else-if="mascotState === 'warning'" src="/nailonghuishou.webm" class="mascot" autoplay loop muted></video>
    </div>

    <el-dialog v-model="addFormVisible" title="📥 录入食材 (支持自由文本)" width="400px" custom-class="cyber-dialog">
      <el-form :model="addForm" label-width="90px">
        <el-form-item label="食材名称">
          <el-select 
            v-model="addForm.ingredientInput" 
            filterable 
            allow-create 
            default-first-option
            placeholder="选择或输入新食材" 
            style="width: 100%;">
            <el-option v-for="dict in dictItems" :key="dict.id" :label="dict.name" :value="dict.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="存储环境">
          <el-radio-group v-model="addForm.storageType">
            <el-radio-button :label="0">冷冻</el-radio-button>
            <el-radio-button :label="1">冷藏</el-radio-button>
            <el-radio-button :label="2">常温</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="当前温度">
          <el-input-number v-model="addForm.currentTemp" :min="-20" :max="40" :step="0.5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addFormVisible = false">取消</el-button>
        <el-button type="primary" class="cyber-btn" @click="submitAdd" :loading="adding">AI 分析入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'

const API_BASE = 'http://localhost:8080/api/pantry'

const dictItems = ref([])
const fridgeItems = ref([])

// 看板娘状态机：'idle' (待机), 'happy' (开心), 'warning' (警告/挥手)
const mascotState = ref('idle')
let mascotTimer = null

const changeMascotState = (state, duration = 4000) => {
  mascotState.value = state
  if (mascotTimer) clearTimeout(mascotTimer)
  mascotTimer = setTimeout(() => {
    mascotState.value = 'idle'
  }, duration)
}

const pokeMascot = () => { changeMascotState('happy', 2000) }

// --- 弹窗与表单 ---
const addFormVisible = ref(false)
const adding = ref(false)
const addForm = reactive({
  ingredientInput: null, // 可以是 ID (数字) 或者 手打的字符串
  storageType: 1,
  currentTemp: 4.0,
  initialStatus: 5
})

// AI 2 状态
const recipeSelection = ref([])
const checking = ref(false)
const harmonyResultVisible = ref(false)
const harmonyScore = ref(0)
const harmonyText = ref('')

onMounted(() => {
  fetchDict()
  fetchFridge()
})

const fetchDict = async () => {
  const res = await axios.get(`${API_BASE}/dict`)
  dictItems.value = res.data
}

const fetchFridge = async () => {
  const res = await axios.get(`${API_BASE}/my-fridge`)
  fridgeItems.value = res.data
}

// 提交录入 (彻底解封零样本录入)
const submitAdd = async () => {
  if (!addForm.ingredientInput) {
    ElMessage.warning('请输入或选择食材')
    return
  }
  adding.value = true
  
  try {
    // 直接把 ingredientInput (无论是数字还是手打的中文字符串) 扔给 Java 中枢
    const payload = { ...addForm }
    const res = await axios.post(`${API_BASE}/add`, payload)
    
    ElNotification({ title: '神经网络处理完毕 🤖', message: res.data, type: 'success' })
    addFormVisible.value = false
    
    // 刷新冰箱和大屏词典 (因为词典可能被 LLM 动态扩充了)
    fetchDict()
    fetchFridge() 
    changeMascotState('happy', 3000) // 奶龙开心迎接新食物
  } catch (error) {
    ElMessage.error('入库失败，请检查网络或 AI 引擎状态')
    changeMascotState('warning', 3000)
  } finally {
    adding.value = false
  }


  try {
    const payload = { ...addForm, ingredientId: finalIngredientId }
    const res = await axios.post(`${API_BASE}/add`, payload)
    ElNotification({ title: '入库成功', message: res.data, type: 'success' })
    addFormVisible.value = false
    fetchFridge()
  } catch (error) {
    ElMessage.error('入库失败')
  } finally {
    adding.value = false
  }
}

// 吃掉与丢弃
const consumeItem = async (id) => {
  await axios.post(`${API_BASE}/consume/${id}`)
  ElMessage.success('干饭成功！')
  changeMascotState('happy') // 奶龙开心吃掉
  fetchFridge()
}

const discardItem = async (id) => {
  await axios.post(`${API_BASE}/discard/${id}`)
  ElMessage.warning('已丢弃，下次注意保鲜哦！')
  changeMascotState('warning') // 奶龙挥手告别
  fetchFridge()
}

// AI 2 推演
const checkRecipe = async () => {
  if (recipeSelection.value.length === 0) return
  checking.value = true
  harmonyResultVisible.value = false
  
  try {
    const res = await axios.post(`${API_BASE}/check-recipe`, { ids: recipeSelection.value })
    const resultStr = res.data
    const scoreMatch = resultStr.match(/味觉和谐度：([\d.]+)分/)
    
    if (scoreMatch) {
      harmonyScore.value = parseFloat(scoreMatch[1])
      harmonyText.value = resultStr.split('。')[1] || resultStr
      harmonyResultVisible.value = true
      
      // 联动奶龙表情
      if (harmonyScore.value >= 70) changeMascotState('happy', 5000)
      else if (harmonyScore.value < 50) changeMascotState('warning', 5000)
    }
  } catch (e) {
    ElMessage.error('AI 引擎掉线')
  } finally {
    checking.value = false
  }
}

// 辅助方法
const getDictName = (id) => dictItems.value.find(d => d.id === id)?.name || '未知'

const getDaysLeftText = (expireDateStr) => {
  if (!expireDateStr) return 'AI 计算中...'
  const diffDays = Math.ceil((new Date(expireDateStr) - new Date()) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return `已过期 ${Math.abs(diffDays)} 天`
  if (diffDays === 0) return '危! 今天过期'
  return `倒计时 ${diffDays} 天`
}

const getFreshnessLevel = (expireDateStr) => {
  const diffDays = Math.ceil((new Date(expireDateStr) - new Date()) / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return 'glow-danger'
  if (diffDays <= 2) return 'glow-warning'
  return 'glow-safe'
}

const harmonyColor = computed(() => {
  if (harmonyScore.value >= 75) return '#00ffcc' // 赛博青
  if (harmonyScore.value >= 50) return '#ffb84d' // 警告黄
  return '#ff3366' // 危险红
})
</script>

<style scoped>
/* 深色赛博朋克 + 毛玻璃 UI 架构 */
.cyber-dashboard {
  min-height: 100vh;
  background-color: #0b0f19;
  color: #e2e8f0;
  padding: 20px;
  position: relative;
  overflow: hidden;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 动态背景光晕 */
.ambient-light {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  z-index: 0;
}
.light-1 { width: 500px; height: 500px; background: rgba(0, 255, 204, 0.15); top: -100px; left: -100px; }
.light-2 { width: 600px; height: 600px; background: rgba(255, 51, 102, 0.1); bottom: -200px; right: -100px; }

.glass-container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
}

.glass-header {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-radius: 16px;
  margin-bottom: 24px;
  padding: 0 30px;
}

.logo { font-size: 26px; font-weight: 900; color: #fff; letter-spacing: 1px; }
.badge { font-size: 12px; background: #00ffcc; color: #000; padding: 2px 6px; border-radius: 4px; vertical-align: top; }
.subtitle { font-size: 13px; color: #94a3b8; margin-top: 5px; }

.glass-card {
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 24px;
  min-height: 700px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.card-title {
  font-size: 20px; font-weight: bold; color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 15px; margin-bottom: 20px;
  display: flex; justify-content: space-between; align-items: center;
}

/* 赛博按钮 */
.cyber-btn {
  background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
  border: none; color: white; font-weight: bold; border-radius: 8px;
}
.cyber-btn:hover { box-shadow: 0 0 15px rgba(0, 198, 255, 0.5); }
.warning-btn { background: linear-gradient(90deg, #ff9900 0%, #ff5500 100%); width: 100%; margin-top: 20px; }

/* 食材卡片 & 呼吸灯特效 */
.glass-item-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px; padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  position: relative; transition: all 0.3s ease;
}
.glass-item-card:hover { transform: translateY(-5px); }

.ing-title { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 8px; }
.ing-date { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.ai-predict span { color: #00ffcc; font-weight: bold; }
.ing-countdown { font-size: 16px; font-weight: 900; margin-top: 10px; text-align: right; }

.action-bar { margin-top: 15px; display: flex; justify-content: space-between; }

/* 危险分级呼吸边缘 */
.glow-safe { border-bottom: 3px solid #00ffcc; }
.glow-warning { border-bottom: 3px solid #ffb84d; box-shadow: 0 5px 15px rgba(255, 184, 77, 0.1); }
.glow-danger { 
  border-bottom: 3px solid #ff3366; 
  box-shadow: 0 0 15px rgba(255, 51, 102, 0.4);
  animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(255, 51, 102, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 51, 102, 0); }
}

/* 结果区 */
.result-box { margin-top: 40px; text-align: center; padding: 30px; background: rgba(0,0,0,0.2); border-radius: 16px; }
.score-display { font-size: 60px; font-weight: 900; text-shadow: 0 0 20px currentColor; }
.score-unit { font-size: 20px; }

/* 看板娘 (右下角悬浮) */
.mascot-container {
  position: fixed; bottom: 20px; right: 20px;
  width: 150px; height: 150px; z-index: 100;
  cursor: pointer; transition: transform 0.2s;
}
.mascot-container:hover { transform: scale(1.1); }
.mascot { width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.5)); }
.idle-anim { animation: float 3s ease-in-out infinite; }
@keyframes float { 0% { transform: translateY(0); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0); } }

/* 修复 Element Plus 弹窗深色样式 */
:deep(.el-dialog) { background: #1e293b !important; border: 1px solid #334155; }
:deep(.el-dialog__title), :deep(.el-form-item__label) { color: #fff !important; }
:deep(.el-input__wrapper), :deep(.el-select__wrapper) { background: #0f172a !important; box-shadow: 0 0 0 1px #334155 inset !important; }
:deep(.el-input__inner) { color: #fff !important; }
</style>