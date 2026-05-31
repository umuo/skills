# 🛡️ 代码安全与 Clean Code 审查速查清单

本清单包含常见的高危安全隐患以及代码清洁度（Clean Code）的经典评估规则，供 Agent 在审查代码时作为强有力的依据。

---

## 🔒 1. 核心安全防御 Checklist (Security Defense)

### 🔑 敏感凭证与硬编码 (Secrets Leak)
*   [ ] 是否存在类似 `const API_KEY = "sk-..."`、`password = "123456"` 的敏感硬编码？
*   [ ] 是否不小心把 `.env` 文件或本地私钥（`id_rsa`）等加入了提交范围？
*   **最佳实践**：敏感配置一律使用环境变量（Environment Variables）读取。

### 💉 输入注入防御 (Injection Attacks)
*   [ ] **SQL 注入**：SQL 语句中是否直接拼接了变量？（如 `SELECT * FROM users WHERE name = '` + user + `'`）
    - **改进**：使用参数化查询（Parameterized Queries）或 ORM 框架。
*   [ ] **XSS 注入**：Web 页面上是否在未做转义（escape）的情况下，直接通过 `innerHTML` 或前端模板渲染了用户输入的原始数据？
    - **改进**：使用 textContent，或采用经过 XSS 过滤的框架绑定。
*   [ ] **OS 命令注入**：Node.js 等后端环境中是否使用了 `child_process.exec(cmd)` 且 `cmd` 拼接了未经校验的用户输入？

### 🌐 安全控制与逻辑越权 (Broken Access Control)
*   [ ] **水平越权**：查询订单、修改用户信息时，后端接口是否只凭 `orderId` 查询，而未核对当前登录用户是否是该订单的拥有者？
*   [ ] **垂直越权**：管理员专属接口，是否有拦截器或中间件（Middleware）校验当前用户的 Role 权限？

---

## 🧹 2. Clean Code 清洁代码 Checklist

### 🏷️ 命名黄金法则 (Meaningful Names)
*   [ ] **名副其实**：变量和方法名必须能回答“它为什么存在、它做什么、它怎么用”。拒绝单字母变量名（除了短循环中的 `i`, `j`）以及无意义的名称如 `data`, `temp`, `info`。
*   [ ] **读得出来**：避免使用中文拼音混搭，甚至拼音首字母缩写（例如 `yhgl` 代表用户管理）。

### 🧩 函数（Methods）设计规范
*   [ ] **单一职责**：一个函数应该只做一件事，且做好这件事。
*   [ ] **短小精悍**：单函数行数建议控制在 **50 行** 以内。如果超过，尝试将内部的逻辑块抽离为独立的私有辅助方法。
*   [ ] **参数精简**：函数的参数数量最好不要超过 **3 个**。若参数过多，应封装成参数对象（Object / DTO）。
*   [ ] **减少嵌套**：通过卫语句（Guard Clauses）尽早 `return` 或抛出异常，消除过深的 `if-else` 或循环嵌套。

---

## 🛠️ 3. 健壮性 Checklist (Robustness)

### 🛑 异常处理 (Exception Handling)
*   [ ] 异步操作是否都有 `try-catch` 或 `.catch()` 处理？
*   [ ] 捕获了异常后，是否只写了空闭合块（默默吞掉异常而不做任何日志输出或提示）？
*   [ ] 涉及资源（如文件、Socket、Database 链接）的操作是否在 `finally` 块中确保能安全释放？
