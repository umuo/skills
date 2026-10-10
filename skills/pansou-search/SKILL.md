---
name: pansou-search
description: 搜索并获取各类网盘资源（电影、剧集、学习课程、电子书、软件等）。支持限定网盘类型（如 aliyun, quark, baidu, tianyi, 115）、指定数据源（tg, plugin, all）、关键词包含与排除过滤、时间倒序整理，并提取网盘直链与提取码。
---

# 盘搜 (PanSou) 网盘资源检索技能

本技能封装了基于 PanSou 服务的全套网盘资源检索与过滤操作（源自 `PanSouTool.java`）。当用户需要查找影视资源、动漫、电子书、课程、软件，或希望获取特定网盘的分享链接及提取码时激活。

---

## 🎯 触发场景与激活条件

当用户提出类似以下请求时调用：
- *“帮我找一下《繁花》的夸克或阿里网盘资源”*
- *“搜索 Python 全套视频教程，要有提取码的，只要百度网盘”*
- *“找一下 Photoshop 2024 安装包，排除 Mac 版本的”*
- *“查一下有没有考公考研的资料，刷新一下缓存”*

---

## 🛠️ 参数规范与配置

### 1. 核心参数映射

| 参数名 | 对应字段 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| **关键词 (必填)** | `kw` | String | 检索核心名称，自动去除首尾空格 | `"流浪地球2 4K"` |
| **数据源** | `src` | String | 来源渠道：`all` (全部)、`tg` (Telegram 频道)、`plugin` (扩展插件)，默认 `all` | `"all"` |
| **网盘类型** | `cloud_types` | List\<String\> | 限定网盘，如 `aliyun`, `quark`, `baidu`, `tianyi`, `115`, `xunlei`, `lanzou` | `["quark", "aliyun"]` |
| **指定插件** | `plugins` | List\<String\> | 指定特定检索插件名 | `["tg_search"]` |
| **包含关键词 (OR)** | `filter.include` | List\<String\> | 结果标题或内容中**至少包含其一** | `["4K", "杜比"]` |
| **排除关键词 (OR)** | `filter.exclude` | List\<String\> | 结果标题或内容中**包含任意一个则过滤** | `["预告", "枪版"]` |
| **强制刷新缓存** | `refresh` | Boolean | 跳过服务端缓存，实时请求各渠道源（默认 `false`） | `true` |
| **结果归并** | `res` | String | 统一固定为 `"merge"`，按网盘类型归并结果 | `"merge"` |

### 2. 账号认证与本地持久化缓存

首次使用或访问受限时，脚本支持**引导用户配置账号密码并本地持久化缓存**，后续使用无需重复输入。

* **配置文件路径**：`~/.config/pansou/config.json`（自动设置 `0600` 权限以保障敏感凭据安全）。
* **Token 缓存路径**：`~/.cache/pansou/token_<hash>.json`（自动维护 60 秒容错缓冲区）。
* **配置优先级**：命令行显式传参 > 环境变量（`PANSOU_USERNAME` / `PANSOU_PASSWORD`） > 本地持久化配置缓存 > 终端交互式引导。

#### 账号管理命令
```bash
# 首次交互式配置账号（自动验证连接、登录并保存）
python3 "<skill-dir>/scripts/search.py" --configure

# 命令行静默配置（适合脚本或自动化环境）
python3 "<skill-dir>/scripts/search.py" --configure --username "your_user" --password "your_pass"

# 查看当前配置状态（账号脱敏显示，隐藏密码）
python3 "<skill-dir>/scripts/search.py" --show-config

# 清除已保存的账号配置及 Token 缓存
python3 "<skill-dir>/scripts/search.py" --clear-config
```

> [!TIP]
> 脚本会在**首次运行无凭据**或**服务端返回 401 未授权**时，自动触发认证引导；用户输入凭证并成功通过 `/api/auth/login` 校验后，将自动保存配置，后续搜索将直接使用缓存的凭据与 Token。

---

## 🚀 执行方式

### 方式一：使用内置 Python 脚本（推荐）

本技能内置了无需第三方依赖的标准 Python 脚本（仅依赖 Python 3 标准库）：

```bash
# 1. 基础搜索
python3 "<skill-dir>/scripts/search.py" "庆余年2"

# 2. 限定特定网盘类型（如阿里与夸克）
python3 "<skill-dir>/scripts/search.py" "三体" --cloud-types "aliyun,quark"

# 3. 带高级过滤（必须包含 4K/HDR，排除预告/枪版）
python3 "<skill-dir>/scripts/search.py" "阿凡达" --include "4K,HDR" --exclude "预告,枪版"

# 4. 指定数据来源与强制刷新缓存
python3 "<skill-dir>/scripts/search.py" "黑神话悟空" -s tg -r

# 5. 输出结构化 JSON 或导出文件
python3 "<skill-dir>/scripts/search.py" "考研数学" --format json --output /tmp/math_res.json
```

### 方式二：直接 HTTP API 调用 (Curl / 语言客户端)

#### 1. 登录鉴权 (若配置了用户凭证)
```bash
curl -s -X POST "https://pansou.lacknb.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"<username>","password":"<password>"}'
```
响应结构示例：
```json
{
  "token": "eyJhbGciOi...",
  "expires_at": 1740000000
}
```

#### 2. 发起网盘检索
```bash
curl -s -X POST "https://pansou.lacknb.com/api/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "kw": "深度学习 视频",
    "res": "merge",
    "src": "all",
    "cloud_types": ["baidu", "aliyun"],
    "filter": {
      "include": ["网盘", "视频"],
      "exclude": ["失效"]
    },
    "refresh": false
  }'
```

---

## 📊 响应解析与格式化规则

### 1. 兼容性解析
- **外层包装**：优先取 `response.data`，若无则使用顶层 JSON。
- **分组归并**：
  - 优先读取 `merged_by_type`（结构为 `{"quark": [...], "aliyun": [...]}`）。
  - 若 `merged_by_type` 为空，降级遍历 `results` 数组，从每个项的 `links` 提取 `type`（缺失默认 `others`），将 `title` 或 `content` 填入 `note`，手动按网盘类型归并。

### 2. 排序与截断规范
- **时间倒序**：对每个网盘分类下的链接列表，解析 `datetime`（ISO 8601 OffsetDateTime，如 `2024-05-01T12:00:00+08:00`）。无效时间（如以 `0001-01-01` 开头或解析失败）按时间戳 0 处理并置底，将**最新发布的资源排在前面**。
- **展示条数**：每个网盘分类默认取最新的前 10 条，避免信息过载。

### 3. Agent 标准输出展示格式
呈现给用户时，应遵循清晰整洁的中文格式：

```text
网盘搜索结果（共 32 条）：

【aliyun】
庆余年第二季 4K 纯净版全集 [更新至完结]
https://www.alipan.com/s/xxxxxx 提取码：abcd

【quark】
庆余年 S02 2160p 高码率收藏版
https://pan.quark.cn/s/yyyyyy

【baidu】
[2024] 庆余年 2 1080P 高清国语
https://pan.baidu.com/s/zzzzzz 提取码：8888
```

---

## ⚠️ 异常处理与边界情况

1. **关键词为空**：直接拦截并提示“搜索关键词不能为空”。
2. **401 Unauthorized**：若提供了用户名与密码，清空本地 Token 缓存后重新发起 `/api/auth/login`，重试检索请求一次。
3. **超时与网络波动**：连接超时建议 10s，读取超时建议 45s（网盘聚合需拉取多个外部插件，耗时较长）。遇超时向用户说明可能上游源响应较慢，可建议缩小 `cloud_types` 或重试。
4. **空结果处理**：未匹配到任何可用网盘链接时，友好提示“没有找到相关网盘资源”，并建议精简或更换关键词。
