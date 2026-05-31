---
name: git-conventional-commit
description: 帮助 Agent 根据当前工作区变更自动生成符合 Conventional Commits 规范的 Git Commit 消息并规范化提交流程。
version: 1.0.0
tags: [git, workflow, productivity]
---

# 📝 Git 自动规范提交技能 (git-conventional-commit)

本技能旨在帮助 AI Agent 分析当前工作区的文件变动（`git diff`），自动提炼符合 Conventional Commits 规范的 Commit Message，并辅助开发者完成规范、优美的 Git 提交记录。

## 🎯 触发场景与激活条件
当用户发出类似以下指令时，自动激活并应用本技能的 Playbook 规则：
- *“帮我提交一下代码”*
- *“自动生成 commit message”*
- *“把刚刚修改的内容 push 到仓库”*
- *“生成 conventional commit”*

---

## 📋 核心运行手册 (Playbook)

请 AI Agent 严格按照以下流程处理 Git 提交任务：

### 第一步：获取当前工作区状态与 Diff
1. 执行 `git status` 确认哪些文件被修改，哪些被暂存（staged）。
2. 如果没有任何文件被暂存，执行 `git diff` 查看未暂存的更改，并询问用户是否将所有更改暂存（即执行 `git add -A` 或 `git add <具体文件>`）。
3. 执行 `git diff --cached` 获取已暂存的详细代码变动。

### 第二步：分析变动，判定 Conventional Commits 类型
阅读变动代码，根据以下原则判定本次提交的主类型：
*   **feat**: 新增了功能（Feature）。
*   **fix**: 修复了 Bug/漏洞。
*   **docs**: 仅修改了文档、README 等。
*   **style**: 仅修改了格式、排版、美化，不改变代码逻辑（如缩进、空格、分号等，注意：这与 CSS 视觉美化不同，CSS 样式新增/变更仍推荐为 feat 或 style，但如果是单纯格式化，使用 style）。
*   **refactor**: 代码重构（既不修复 Bug 也不增加新功能的代码更改）。
*   **perf**: 提升了性能的代码更改。
*   **test**: 添加或修改测试代码。
*   **chore**: 构建流程、依赖管理或辅助工具的变动（如修改 `.gitignore`, `package.json` 依赖等）。

### 第三步：撰写符合规范的提交消息
按照以下标准格式（中文）生成 Commit Message：

```text
<type>(<scope>): <subject>

<body>

<footer>
```

*   **Header (首行，字数控制在 50 字以内)**:
    - 格式：`<type>(影响的模块/范围): 简短精炼的中文总结（动词开头，如“新增...”、“修复...”）`。
    - 示例：`feat(auth): 新增用户手机号验证登录功能`
*   **Body (空一行后的详细描述，非必选，但复杂修改必须有)**:
    - 换行说明具体做了什么改动，以及为什么这么做。
    - 保持精练，每行不超过 72 个字符。
*   **Footer (空一行后的底部信息，非必选)**:
    - 关联的 Issue（如 `Closes #123`），或声明 Breaking Change。

### 第四步：展示并确认
1. 将拟定好的 Commit Message 呈现给用户，格式如下：
   > 🔍 **为您拟定的规范 Commit Message：**
   > ```text
   > feat(core): 初始化基础配置文件
   > 
   > - 新增 README.md 文档，介绍多技能仓库规范
   > - 新增 .gitignore，过滤 OS 及编辑器缓存文件
   > ```
2. 询问用户是否同意该提交。
3. 用户确认后，运行 `git commit -m "<message>"` 完成提交。

---

## 📚 辅助参考
若需要更详尽的 Conventional Commits 标准说明，请参考并读取：
[conventional-commits.md](references/conventional-commits.md)
