# 📘 Conventional Commits 约定式提交规范速查表

约定式提交规范是一种基于提交消息的轻量级约定。它提供了一套简单易懂的规则来创建清晰的提交历史，这使得编写自动化工具（如生成 Changelog、判定版本号等）变得更加容易。

## 🏗️ 提交信息基本格式

每个提交消息都包含一个**页眉（header）**、一个**正文（body）**和一个**页脚（footer）**。页眉具有特殊的格式，包含**类型（type）**、**作用域（scope，可选）**和**描述（description）**：

```text
<type>(<scope>): <description>

[body]

[footer(s)]
```

---

## 🏷️ 核心提交类型 (Commit Types)

| 类型 | 意义 | 适用场景 |
| :--- | :--- | :--- |
| **feat** | 新特性 (Feature) | 在代码库中新增了某个功能或模块。 |
| **fix** | 修复 (Bug Fix) | 修复了代码库中的漏洞、异常或已知 Bug。 |
| **docs** | 文档变更 (Documentation) | 仅修改了文档、注释、说明书，未修改逻辑代码。 |
| **style** | 样式/格式 (Style) | 不影响代码运行逻辑的纯格式更改（如空格、格式化、缺少分号）。 |
| **refactor** | 重构 (Refactoring) | 既不修复 Bug 也不添加新功能的代码结构重组或重构。 |
| **perf** | 性能提升 (Performance) | 提高了运行效率、减少了内存消耗的代码变动。 |
| **test** | 测试 (Tests) | 新增测试用例，或更正、补充现有测试。 |
| **build** | 构建系统 (Build) | 影响构建系统或外部依赖项的更改（如 gulp、webpack、npm）。 |
| **ci** | 持续集成 (CI) | 修改 CI 配置文件和脚本（如 GitHub Actions, Travis）。 |
| **chore** | 杂务 (Chore) | 其他不修改 src 或测试文件的辅助性修改（如 `.gitignore`）。 |
| **revert** | 撤销 (Revert) | 撤销之前的某次 Git 提交。 |

---

## ⚠️ 重大变更 (Breaking Changes)

重大变更代表本次提交包含不向后兼容的修改。它有两种声明方式：
1. 在类型/作用域后添加 `!`。例如：
   `feat(api)!: 重构接口签名，取消原有 Token 校验机制`
2. 在 `footer` 部分以 `BREAKING CHANGE:` 开头进行描述。例如：
   ```text
   refactor(auth): 升级加密算法

   BREAKING CHANGE: 原有的 MD5 散列算法已全面停用，所有本地数据库密码需要强制重置。
   ```

---

## 📝 优秀提交示例

### 示例 1：简明的新功能提交
```text
feat(auth): 新增邮箱验证码登录功能

- 支持 6 位动态验证码发送
- 新增验证码过期时间限制（5分钟）
- 增加防刷机制（同邮箱 60 秒内限发一次）
```

### 示例 2：Bug 修复并关联 Issue
```text
fix(cart): 修复结算页面多次快速点击导致的重复下单问题

防止在向后端发送订单请求时，按钮未被及时禁用而发生的重复提交。

Closes #409
```
