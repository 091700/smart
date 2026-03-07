<template>
  <div class="dashboard-container">
    <el-container>
      <el-header height="80px" class="header">
        <div class="logo">🍱 SmartPantry 智惠便当盒</div>
        <div class="subtitle">基于 PyTorch 双核 AI 驱动的家庭防浪费中枢</div>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :span="16">
            <el-card class="box-card fridge-card">
              <template #header>
                <div class="card-header">
                  <span>❄️ 我的虚拟冰箱 (AI 1 动态保鲜监控)</span>
                  <el-button type="primary" size="large" @click="addFormVisible = true">
                    <el-icon><Plus /></el-icon> 扫码/录入新食材
                  </el-button>
                </div>
              </template>
              
              <el-empty v-if="fridgeItems.length === 0" description="冰箱空空如也，快去进货吧！" />

              <el-row :gutter="15" v-else>
                <el-col :span="8" v-for="item in fridgeItems" :key="item.id" style="margin-bottom: 15px;">
                  <el-card shadow="hover" :class="['ingredient-card', getFreshnessLevel(item.predictedExpireDate)]">
                    <div class="ing-title">{{ getDictName(item.ingredientId) }}</div>
                    <div class="ing-info">入库时间：{{ item.entryDate }}</div>
                    <div class="ing-info">
                      预计变质：<strong>{{ item.predictedExpireDate }}</strong>
                    </div>
                    <div style="margin-top: 10px; text-align: right;">
                      <el-tag :type="getTagType(item.predictedExpireDate)" effect="dark">
                        {{ getDaysLeftText(item.predictedExpireDate) }}
                      </el-tag>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card class="box-card dark-magic-card">
              <template #header>
                <div class="card-header">
                  <span>🔮 暗黑料理避雷针 (AI 2)</span>
                </div>
              </template>
              <div class="magic-desc">
                突发奇想？选中你想混搭的食材，AI 神经元将自动推演它们在多维味觉空间中的碰撞结果！
              </div>
              
              <el-select 
                v-model="recipeSelection" 
                multiple 
                :multiple-limit="3"
                placeholder="请选择 1~3 种食材组合" 
                style="width: 100%; margin-bottom: 20px;"
                size="large">
                <el-option v-for="dict in dictItems" :key="dict.id" :label="dict.name" :value="dict.id" />
              </el-select>
              
              <el-button type="warning" size="large" style="width: 100%; font-weight: bold;" @click="checkRecipe" :loading="checking">
                <el-icon><MagicStick /></el-icon> 召唤 AI 进行味觉推演
              </el-button>

              <div v-if="harmonyResultVisible" class="result-box">
                <el-progress 
                  type="dashboard" 
                  :percentage="harmonyScore" 
                  :color="harmonyColor"
                  :width="150"
                  :stroke-width="12">
                  <template #default="{ percentage }">
                    <span class="percentage-value">{{ percentage }}分</span>
                  </template>
                </el-progress>
                <div class="harmony-text" :style="{ color: harmonyColor }">{{ harmonyText }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <el-dialog v-model="addFormVisible" title="📥 录入新食材 (召唤 AI 1)" width="400px">
      <el-form :model="addForm" label-width="90px">
        <el-form-item label="选择食材">
          <el-select v-model="addForm.ingredientId" placeholder="扫描或选择食材" style="width: 100%;">
            <el-option v-for="dict in dictItems" :key="dict.id" :label="dict.name" :value="dict.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="存储方式">
          <el-radio-group v-model="addForm.storageType">
            <el-radio-button :label="0">冷冻</el-radio-button>
            <el-radio-button :label="1">冷藏</el-radio-button>
            <el-radio-button :label="2">常温</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="当前温度(℃)">
          <el-input-number v-model="addForm.currentTemp" :min="-20" :max="40" :step="0.5" />
        </el-form-item>
        <el-form-item label="初始新鲜度">
          <el-rate v-model="addForm.initialStatus" :max="5" show-score text-color="#ff9900" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addFormVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAdd" :loading="adding">
            放进冰箱并预测
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElNotification } from 'element-plus'

// 全局配置 Java 后端的地址
const API_BASE = 'http://localhost:8080/api/pantry'

// --- 状态数据 ---
const dictItems = ref([])
const fridgeItems = ref([])

// 弹窗与表单
const addFormVisible = ref(false)
const adding = ref(false)
const addForm = reactive({
  ingredientId: null,
  storageType: 1, // 默认冷藏
  currentTemp: 4.0,
  initialStatus: 5 // 默认满分新鲜
})

// AI 2 味觉推演状态
const recipeSelection = ref([])
const checking = ref(false)
const harmonyResultVisible = ref(false)
const harmonyScore = ref(0)
const harmonyText = ref('')

// --- 初始化生命周期 ---
onMounted(() => {
  fetchDict()
  fetchFridge()
})

// --- 核心方法 ---

// 1. 获取字典库
const fetchDict = async () => {
  try {
    const res = await axios.get(`${API_BASE}/dict`)
    dictItems.value = res.data
  } catch (error) {
    ElMessage.error('无法连接到 Java 后端，请检查 8080 端口！')
  }
}

// 2. 获取冰箱物品
const fetchFridge = async () => {
  try {
    const res = await axios.get(`${API_BASE}/my-fridge`)
    fridgeItems.value = res.data
  } catch (error) {
    console.error(error)
  }
}

// 3. 提交新食材 (召唤 AI 1)
const submitAdd = async () => {
  if (!addForm.ingredientId) {
    ElMessage.warning('请选择一种食材！')
    return
  }
  adding.value = true
  try {
    const res = await axios.post(`${API_BASE}/add`, addForm)
    // 成功后给予炫酷提示
    ElNotification({
      title: 'AI 预测完成 🤖',
      message: res.data,
      type: 'success',
      duration: 5000
    })
    addFormVisible.value = false
    fetchFridge() // 刷新冰箱
  } catch (error) {
    ElMessage.error('存入失败！')
  } finally {
    adding.value = false
  }
}

// 4. 味觉推演 (召唤 AI 2)
const checkRecipe = async () => {
  if (recipeSelection.value.length === 0) {
    ElMessage.warning('请至少选择1种食材！')
    return
  }
  checking.value = true
  harmonyResultVisible.value = false
  
  try {
    const res = await axios.post(`${API_BASE}/check-recipe`, { ids: recipeSelection.value })
    // 解析返回的文本提取分数 (Java 端返回类似 "味觉和谐度：85.5分。绝妙搭配...")
    const resultStr = res.data
    const scoreMatch = resultStr.match(/味觉和谐度：([\d.]+)分/)
    
    if (scoreMatch) {
      harmonyScore.value = parseFloat(scoreMatch[1])
      harmonyText.value = resultStr.split('。')[1] || resultStr
      harmonyResultVisible.value = true
    } else {
       ElMessage.info(resultStr)
    }
  } catch (error) {
    ElMessage.error('推演失败，AI 引擎可能已掉线！')
  } finally {
    checking.value = false
  }
}

// --- 辅助显示方法 (让界面变聪明的核心) ---

// 根据字典ID找名字
const getDictName = (id) => {
  const item = dictItems.value.find(d => d.id === id)
  return item ? item.name : '未知食材'
}

// 计算剩余天数并返回文字
const getDaysLeftText = (expireDateStr) => {
  if (!expireDateStr) return '计算中'
  const today = new Date()
  const expDate = new Date(expireDateStr)
  const diffTime = expDate - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return `已过期 ${Math.abs(diffDays)} 天 ☠️`
  if (diffDays === 0) return '今天变质 ⚠️'
  return `还能放 ${diffDays} 天`
}

// 根据剩余时间给出卡片的危险颜色等级 (CSS 类名)
const getFreshnessLevel = (expireDateStr) => {
  const today = new Date()
  const expDate = new Date(expireDateStr)
  const diffDays = Math.ceil((expDate - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'level-danger' // 红色
  if (diffDays <= 2) return 'level-warning' // 黄色
  return 'level-safe' // 绿色
}

// Element Plus 标签颜色
const getTagType = (expireDateStr) => {
  const level = getFreshnessLevel(expireDateStr)
  if (level === 'level-danger') return 'danger'
  if (level === 'level-warning') return 'warning'
  return 'success'
}

// AI 2 仪表盘颜色计算
const harmonyColor = computed(() => {
  if (harmonyScore.value >= 70) return '#67C23A' // 绿色：好吃
  if (harmonyScore.value >= 40) return '#E6A23C' // 黄色：凑合
  return '#F56C6C' // 红色：拉肚子
})
</script>

<style scoped>
/* 自定义赛博农家乐风格 UI */
.dashboard-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  padding: 20px;
}

.header {
  background: linear-gradient(135deg, #1890ff 0%, #364d79 100%);
  color: white;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-bottom: 20px;
  padding-left: 30px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.logo {
  font-size: 28px;
  font-weight: bold;
}

.subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
}

.fridge-card {
  min-height: 700px;
}

.dark-magic-card {
  background: #fafafa;
  border-top: 4px solid #E6A23C;
}

.magic-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 20px;
  line-height: 1.6;
}

/* 食材卡片样式 */
.ingredient-card {
  border-radius: 8px;
  transition: all 0.3s;
  border-left: 5px solid #ebeef5;
}
.ingredient-card:hover {
  transform: translateY(-5px);
}

.ing-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 10px;
  color: #303133;
}

.ing-info {
  font-size: 13px;
  color: #606266;
  margin-bottom: 5px;
}

/* 危险等级颜色 */
.level-safe { border-left-color: #67C23A; }
.level-warning { 
  border-left-color: #E6A23C; 
  background-color: #fdf6ec;
}
.level-danger { 
  border-left-color: #F56C6C; 
  background-color: #fef0f0;
  opacity: 0.8;
}

/* AI2 结果区 */
.result-box {
  margin-top: 40px;
  text-align: center;
  padding: 20px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}

.percentage-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.harmony-text {
  margin-top: 15px;
  font-size: 16px;
  font-weight: bold;
}
</style>