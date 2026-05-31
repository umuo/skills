# 💡 My Agent Skills - 常用 AI Agent 技能仓库

这是一个遵循 [skills.sh](https://skills.sh) 规范的 AI Agent 技能（Skills）仓库。本仓库用于收集、管理和分发日常开发中高频使用的 AI Agent 技能，以模块化的指令和知识库，赋予 AI 编码助手（如 Claude Code, Cursor, Windsurf 等）专业化的能力。

> [!NOTE]
> **什么是 Agent Skill？**  
> Agent Skill 是一种可复用、模块化的 AI 提示词与工具集。它由一个包含 YAML 元数据的 `SKILL.md` 文件及其辅助的脚本、参考文档组成。AI 代理会在检测到需要相关能力时自动装载这些技能，从而提供比普通提示词更可靠、更专业的操作行为。

---

## 📂 目录结构与规范

本仓库采用多技能（Multi-skill）存储结构。每一个子目录都代表一个独立的技能包：

```text
.
├── README.md                           # 仓库使用指南
├── .gitignore                          # 基础 Git 忽略规则
└── skills/                             # 技能存放目录
    ├── git-conventional-commit/        # 技能 1：Git Conventional 自动提交规范技能
    ├── code-clean-reviewer/            # 技能 2：高级代码清洁与安全审查技能
    └── frontend-ui-polisher/           # 技能 3：前端 UI 现代视觉与微动效打磨技能
```

### 🛠️ 技能包的组成规范
每个技能包应当遵循以下结构：
1. **`SKILL.md` (必须)**: 顶部的 YAML Frontmatter 定义技能名称与触发描述，正文为 Playbook 运行手册。
2. **`references/` (可选)**: 存放重度背景知识、协议、速查表（Cheatsheets）。
3. **`scripts/` (可选)**: 存放辅助自动化脚本，供 Agent 运行时调用。
4. **`assets/` (可选)**: 存放 UI 模板、图标、设计图等静态资源。

---

## ⚡ 预置技能列表

### 1. 📝 Git 自动规范提交 (`git-conventional-commit`)
*   **用途**：当你想生成符合规范的提交消息或进行 Git 提交时激活。
*   **特性**：自动分析 `git diff`，依据 Conventional Commits 标准判定类型（`feat`, `fix`, `docs` 等），并自动以精练的中文编写规范的提交信息。
*   **入口路径**：[skills/git-conventional-commit/](skills/git-conventional-commit/SKILL.md)

### 2. 🔍 高级代码清洁与安全审查 (`code-clean-reviewer`)
*   **用途**：在提交代码或合并 PR 前进行静态安全与质量审查。
*   **特性**：寻找硬编码密钥、SQL 注入、XSS、逻辑死循环、资源泄漏，并基于 Clean Code 原则优化命名、降低圈复杂度。
*   **入口路径**：[skills/code-clean-reviewer/](skills/code-clean-reviewer/SKILL.md)

### 3. 🎨 前端 UI/微动效打磨 (`frontend-ui-polisher`)
*   **用途**：当需要优化网页 UI 视觉效果、编写 CSS 或提升用户交互体验时激活。
*   **特性**：指导 Agent 引入毛玻璃、高级渐变色、平滑微悬浮交互 and 高水准 HSL 配色方案，拒绝简陋粗糙的默认样式。
*   **入口路径**：[skills/frontend-ui-polisher/](skills/frontend-ui-polisher/SKILL.md)

---

## ⚙️ 如何使用

### 1. 本地直接激活 (推荐)
如果您在本地的 AI 编码工具（如 Claude Code）中工作，可以通过配置将本仓库的 `skills` 目录添加到您的全局或项目技能扫描路径中：
* **Claude Code 全局路径**：将技能文件夹复制到 `~/.claude/skills/` 
* **项目局部路径**：将本仓库中的特定技能文件夹放置到您项目目录下的 `.claude/skills/` 

### 2. 借助 skills.sh CLI 管理
本仓库的技能可以通过 `skills.sh` 官方 CLI 工具进行添加与管理：
```bash
# 激活/添加指定技能
npx skills add <your-github-username>/skills/skills/git-conventional-commit

# 查看已安装技能
npx skills list
```

---

## 💡 如何贡献或新增技能

1. 在 `skills/` 目录下创建一个新的文件夹，例如 `skills/my-new-skill/`。
2. 在该文件夹下新建 `SKILL.md`。
3. 仿照现有技能在文件顶部添加 YAML Frontmatter，设定独特的 `name`（建议与文件夹同名）与精准的 `description`。
4. 编写清晰、结构化的 Markdown 指引 Playbook。
5. 提交并推送到您的 GitHub 远程仓库。
