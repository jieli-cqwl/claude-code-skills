---
name: h5
command: h5
user_invocable: true
description: |
  H5 移动端交互体验优化助手（UniApp + Vue3 技术栈）。自动激活场景：
  1) 开发 H5 组件、移动端页面时
  2) 讨论触摸交互、手势操作、动画效果时
  3) 处理加载状态、错误提示、表单验证时
  无需特别关键词，只要涉及「H5」「移动端」「触摸」「滑动」「加载」就自动融入
  60fps 流畅动画、即时触摸反馈、容错友好的交互体验。
---

# H5 移动端开发规范（UniApp + Vue3）

> 基于 qft-harmonyos-vue3 项目 UI 规范，适用于 H5/小程序/App 多端开发

---

## 一、技术栈

| 类别 | 技术 |
|------|------|
| 框架 | UniApp 3.0 + Vue3 + TypeScript |
| 状态管理 | Pinia |
| UI 组件 | 自定义 comp-xxx + uni-ui |
| 列表分页 | z-paging |
| 样式 | SCSS + rpx 单位 |

---

## 二、颜色系统

### 2.1 品牌色

| 变量 | 色值 | 用途 |
|------|------|------|
| `$text-blue` | #3277FF | 主色、链接、按钮 |
| `$bgc-blue` | #3377FF | 主按钮背景 |
| `$text-blue-light` | #E8F0FF | 浅蓝背景 |

### 2.2 中性色

| 变量 | 色值 | 用途 |
|------|------|------|
| `$text-black` | #333333 | 主要文字 |
| `$text-grey` | #84888F | 次要文字（最常用） |
| `$text-grey-light` | #999999 | 辅助文字 |
| `$bgc-page` | #F1F2F7 | 页面背景（推荐） |
| `$bgc-grey` | #84888F | 特殊标签灰色背景 |
| `$bgc-grey-text` | #EAEDF2 | 灰色字体的背景 |

### 2.3 功能色

| 变量 | 色值 | 用途 |
|------|------|------|
| `$text-red` | #ED184E | 错误、必填标记 |
| `$bgc-red-type-one` | #FF3D6E | 警告按钮 |
| `$bgc-red-type-two` | #FFE0E6 | 浅红背景 |
| `$bgc-red-type-three` | #FBBCCC | 中红背景 |
| `$text-orange` | #FF6A00 | 警告提示 |
| `$bgc-orange` | #FF6A00 | 橙色背景 |
| `$text-yellow` | #D5B62B | 黄色文字 |
| `$text-yellow-bgc` | #7A7667 | 黄色背景上的文字 |
| `$bgc-yellow` | #FAD955 | 黄色背景 |

### 2.4 特殊蓝色

| 变量 | 色值 | 用途 |
|------|------|------|
| `$text-special-blue` | #22ADE3 | 特殊蓝色文字（短租标签等） |
| `$bgc-special-blue-type-one` | #22ADE3 | 特殊蓝背景 |
| `$bgc-special-blue-type-two` | #e9f5fa | 浅特殊蓝背景 |

---

## 三、间距系统（rpx）

| 值 | 用途 | 使用频率 |
|----|------|---------|
| **20rpx** | 常用间距 | 最高频 |
| 32rpx | 页面/卡片内边距 | 高频 |
| 24rpx | 中等间距 | 中频 |
| 16rpx | 小间距 | 中频 |
| 8rpx | 紧凑间距 | 低频 |

---

## 四、字体系统（rpx）

| 大小 | 用途 |
|------|------|
| 24rpx | 辅助说明、标签 |
| **28rpx** | 正文（默认） |
| 32rpx | 小标题 |
| 36rpx | 卡片标题 |
| 40rpx | 页面标题 |

---

## 五、组件命名规范

### 5.1 命名格式

```
comp-{功能描述}[-{变体}]
```

### 5.2 常用组件

| 组件 | 用途 |
|------|------|
| `comp-popup` | 底部弹窗基础 |
| `comp-popup-tips` | 提示类弹窗 |
| `comp-popup-picker` | 选择器弹窗 |
| `comp-dropmenu-new` | 下拉筛选菜单 |
| `comp-form-configure` | JSON Schema 动态表单 |
| `comp-notice` | Toast/Loading 提示 |
| `comp-empty` | 空状态 |

---

## 六、核心交互原则

### 6.1 三个即时原则

| 原则 | 标准 | 说明 |
|------|------|------|
| **即时反馈** | < 100ms | 触摸后立即有视觉变化 |
| **流畅动画** | 60fps | 只用 transform/opacity |
| **容错友好** | 0 困惑 | 错误提示说人话、给出路 |

### 6.2 移动端特性

- **触摸目标**：≥ 88rpx (44px)，间距 ≥ 16rpx
- **竖屏优先**：核心功能在拇指热区
- **安全区域**：底部按钮需适配 safe-area-inset-bottom

---

## 七、页面模式

### 7.1 列表页（z-paging）

```vue
<template>
  <z-paging ref="paging" v-model="list" @query="queryList">
    <template #top>
      <!-- 筛选栏 -->
    </template>
    <view v-for="item in list" :key="item.id">
      <!-- 列表项 -->
    </view>
  </z-paging>
</template>
```

### 7.2 表单页（comp-form-configure）

```vue
<comp-form-configure
  :formItemMap="formItemMap"
  :formModel="formModel"
  @submit="onSubmit"
/>
```

### 7.3 多步骤表单（Pinia）

```typescript
// stores/checkin.ts
export const useCheckinStore = defineStore('checkin', {
  state: () => ({
    step: 1,
    formData: {}
  }),
  actions: {
    nextStep() { this.step++ },
    prevStep() { this.step-- },
    saveStepData(data) { Object.assign(this.formData, data) }
  }
})
```

---

## 八、检查清单

### 必查项

- [ ] 颜色使用 SCSS 变量（`$text-blue` 等）
- [ ] 间距使用 rpx 单位（优先 20rpx、32rpx）
- [ ] 字体大小正确（正文 28rpx）
- [ ] 组件命名 `comp-xxx` 格式
- [ ] 触摸目标 ≥ 88rpx

### 交互项

- [ ] 按钮有 loading 状态
- [ ] 表单有验证提示
- [ ] 列表有空状态
- [ ] 错误提示说人话

---

## 九、参考文档

| 文档 | 内容 |
|------|------|
| `references/项目初始化规范.md` | 项目创建、依赖安装、配置文件 |
| `references/目录结构规范.md` | 目录组织、命名规范 |
| `references/路由规范.md` | pages.json、导航、分包 |
| `references/状态管理规范.md` | Pinia 使用规范 |
| `references/TypeScript规范.md` | 类型定义规范 |
| `references/样式系统规范.md` | 颜色、间距、字体、圆角、阴影 |
| `references/组件开发规范.md` | 组件命名、Props、样式组织 |
| `references/页面模式规范.md` | 列表页、表单页、详情页模板 |
| `references/交互组件规范.md` | 弹窗、菜单、提示、空状态 |
| `references/最佳实践.md` | 防抖、键盘、安全区、条件编译 |
