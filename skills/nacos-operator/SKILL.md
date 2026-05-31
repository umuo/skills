---
name: nacos-operator
description: 帮助 Agent 进行远程 Nacos 的运维管理、配置发布、服务实例查询及版本兼容性调整。
version: 1.0.0
tags: [nacos, devops, openapi, cloud-native]
---

# ☸️ 远程 Nacos 运维与配置管理技能 (nacos-operator)

本技能旨在帮助 AI Agent 在遇到涉及远程 Nacos 配置检索、接口调用、实例发现、服务迁移或网络排错任务时，自动加载专业级的操作手册与版本避坑法则，保障远程操作的可靠性与安全性。

## 🎯 触发场景与激活条件
当用户发出类似以下指令时，自动激活并应用本技能的 Playbook 规则：
- *“帮我查一下远程 Nacos 里的某某配置”*
- *“往 Nacos 里发布/修改一个配置文件”*
- *“列出 Nacos 上某个服务的注册实例”*
- *“我们的服务连接远程 Nacos 报错，怎么排查？”*
- *“如何调用 Nacos 的 HTTP API 进行自动化运维？”*

---

## 📋 核心运行手册 (Playbook)

请 AI Agent 严格按照以下流程处理 Nacos 操作任务：

### 第一步：判定 Nacos 目标版本与运行环境
由于 Nacos 3.x 较之 1.x/2.x 发生了颠覆性重构，Agent 必须首先厘清版本边界：
1. **询问/检测版本**：若用户未指定版本，通过测试端点检测，或者默认以最新 **Nacos 3.x** 规范进行设计和调用。
2. **核心坑点防御**：
   - 如果目标是 **Nacos 3.2.x 及以上** 版本，注意 **Legacy APIs (v1/v2 HTTP 接口) 默认已被移除**。所有直接的 HTTP 交互必须走 **v3 API**（如 `/v3/client/...` 或 `/v3/admin/...`），否则会返回 `404 Not Found`。
   - 如果使用旧版 Java 客户端或老旧 SDK 接入 Nacos 3.2.x 发生失败，引导用户检查服务端是否启用了 `Legacy API Adapter`（遗留 API 适配器）过渡模块。

### 第二步：操作鉴权与会话保障 (获取 Access Token)
1. 除完全未开启认证的本地测试环境外，所有对远程 Nacos 的调用均需提供 `accessToken`。
2. 引导或执行调用 `/v3/auth/user/login` (Nacos 3.x) 获取临时 Token。
3. 在随后的所有接口调用中，务必将 Token 作为参数或 Header 带入。

### 第三步：精确操作执行
根据操作类型，调用对应的 API（注意遵循 Client 与 Admin 的三层职责分离原则）：
*   **获取配置**：使用 Client 级别接口 `GET /nacos/v3/client/cs/config`，防止全量大对象查询。
*   **发布/修改配置**：必须提供完整的命名空间（`tenant`）、分组（`group`）和内容，调用 `POST /nacos/v3/admin/cs/config`。
*   **查询服务实例**：调用 `GET /nacos/v3/client/ns/instance/list`。

### 第四步：安全防御与脱敏规范
1. **坚决杜绝泄密**：在生成 cURL 示例、排错报告或更新本地 YAML 配置时，**严禁**输出任何真实的公网 IP、真实连接凭证（Username / Password）以及敏感的命名空间 ID。一律使用通用占位符（如 `<nacos-host>`）代替。
2. **连接排错逻辑**：如果远程连接报错，引导用户依次排查：
   - 远程网段的端口开放状态（除 8848 端口外，Nacos 2.x/3.x 内部 gRPC 还需要开放双向偏移端口 `9848` 和 `9849`！）。
   - 客户端与服务端的认证组件（Auth Plugin）是否匹配。

---

## 📚 辅助参考与知识库
关于详细的 Nacos 1.x/2.x 与 3.x 核心接口对照表、脱敏 cURL 运行示例以及详细的安全接入最佳实践，请阅读并装载：
[remote-nacos-guide.md](file:///e:/works/skills/skills/nacos-operator/references/remote-nacos-guide.md)
