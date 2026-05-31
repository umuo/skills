---
name: frontend-ui-polisher
description: 专门用于前端视觉体验、现代动效、和谐配色以及微交互的细节打磨技能，大幅提升产品的高级感和Wow效果。
version: 1.0.0
tags: [frontend, css, ui, ux, aesthetics]
---

# 🎨 前端 UI 与微动效打磨技能 (frontend-ui-polisher)

本技能旨在帮助 AI Agent 在接到前端组件开发、页面排版设计或 CSS 重构任务时，打破平庸，主动引入现代感十足、质感优雅的 Web 视觉设计方案，为产品增添“Wow Factor”（令人赞叹的高级感）。

## 🎯 触发场景与激活条件
当用户发出类似以下指令时，自动激活并应用本技能的 Playbook 规则：
- *“帮我设计一个登录页面”*
- *“美化一下这个按钮的样式”*
- *“写一个卡片组件，要好看一点”*
- *“加一些高端的动效”*
- *“给这个页面设计一个配色方案”*

---

## 📋 核心运行手册 (Playbook)

当涉及前端 UI、HTML 或 CSS 编写时，AI Agent 必须严格落实以下设计哲学与操作流程：

### 第一步：奠定高端设计语言 (Design System & Tokens)
拒绝任何粗糙的默认样式（如 plain blue 按钮、硬梆梆的纯黑 #000 边框）。一律引入现代 Web 审美标准：
*   **现代字体**：优先引入 Google Fonts（如 `Inter`、`Outfit`、`Plus Jakarta Sans`），摒弃无感情的默认宋体或 Arial。
*   **和谐色彩体系 (HSL / Harmony Palette)**：
    - 主色调避免生硬的纯红/纯蓝。建议采用经过精细调和的色调。例如，深邃商务的极客蓝（`hsl(220, 90%, 56%)`）或高端翡翠绿（`hsl(155, 69%, 40%)`）。
    - 巧用**渐变色**（Gradients），如 `linear-gradient(135deg, hsl(260, 85%, 65%), hsl(310, 80%, 60%))`，让界面显露流光溢彩的效果。
*   **高级阴影与层次**：
    - 拒绝浓重、粗糙的黑色投影。一律使用极具空气感的轻柔环境阴影：
      `box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.08);`。

### 第二步：实施动态交互与微动效 (Micro-interactions)
没有动画的网页是死气沉沉的。通过轻量级的 CSS Transition 与 Keyframes 让界面“活”过来：
1.  **全局平滑过渡**：凡是有 `:hover`、`:focus`、`:active` 的元素，必须添加过渡时间：
    `transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);`。
2.  **悬停微缩放 (Hover Scales)**：
    当鼠标悬停在卡片或按钮上时，产生轻微上浮和投影加深效果：
    `transform: translateY(-4px) scale(1.02);`。
3.  **柔和滑入动画 (Fade-in / Slide-in)**：
    页面加载或列表渲染时，利用 CSS 动画让组件从下方柔和地滑入和淡入，体现出流畅的韵律感。

### 第三步：落地 Premium 设计细节
引入以下两项高端视觉特性，彻底打动用户：
*   **毛玻璃效果 (Glassmorphism)**：
    在背景具有渐变色或图片时，使用半透明背景结合高斯模糊，让容器显得极其 premium：
    `background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.3);`
*   **呼吸式流光按钮 (Glow Effect)**：
    为重要操作按钮（如“注册”、“立即开始”）赋予呼吸般闪烁的底层投影或渐变边框，引导用户操作。

---

## 📚 辅助参考与 CSS 预置模板
若需直接复制和复用已经封装好的高端 CSS 动效、毛玻璃卡片和骨架屏样式，请阅读并装载：
[animation-templates.css](file:///e:/works/skills/skills/frontend-ui-polisher/assets/animation-templates.css)
