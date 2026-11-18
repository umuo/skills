# Solo API 返回值示例

本文档提供 Solo 博客各 API 接口的返回值示例，结合 Solo 4.4.0 源码实现与线上接口实际返回校验整理。

---

## 通用结构 & HTTP 状态码

### 1. 中间件鉴权与网关错误（非 JSON）

当请求缺少 `X-Solo-API-Key`、Key 无效/已禁用/属于旧版失效残留、或角色权限不足时，请求在到达业务 Controller 之前即被 `ConsoleAuthMidware` / `ConsoleAdminAuthMidware` 拦截并返回 **HTML 错误页**（而非 JSON）：

- **HTTP 401 Unauthorized**：返回 HTML（如 `401 Unauthorized!`），表示 API Key 缺失、已禁用、已删除或旧密钥失效。
- **HTTP 403 Forbidden**：返回 HTML，表示当前凭据无权访问。
- **HTTP 404 / 5xx**：返回服务器或反向代理 HTML 错误页。

> **排错提示**：切勿直接用 `curl -s ... | python3 -m json.tool` 解析响应，否则 `401` 返回 HTML 会触发 `Expecting value` 而掩盖真实状态码。请使用 `scripts/solo_api.py` 或 `curl -sS -w "\n%{http_code}"`。

### 2. 业务接口成功与失败响应（HTTP 200 JSON）

通过鉴权后，常规接口返回 HTTP 200 及 JSON 对象，包含 `code` 字段（`/console/export/*` 返回 `application/zip` 二进制流除外）：

```json
// 成功
{ "code": 0, "msg": "操作成功" }

// 失败
{ "code": -1, "msg": "错误描述" }
```

---

## 文章管理

### 列出文章 — `GET /console/articles/status/{status}/{page}/{pageSize}/{windowSize}`

按置顶和文章更新/发布日期排序。列表中**不包含**文章正文（`articleContent`），且 Solo 4.4+ **不返回 `articleViewCount`**（线上读取该字段为 `null`）。

```json
{
    "code": 0,
    "pagination": {
        "paginationPageCount": 100,
        "paginationPageNums": [1, 2, 3, 4, 5]
    },
    "articles": [
        {
            "oId": "1609459200000",
            "articleTitle": "2024 年度技术总结",
            "articleAbstract": "年度技术复盘与架构演进记录...",
            "articleAbstractText": "年度技术复盘与架构演进记录...",
            "articleTags": "年度总结,技术",
            "articlePermalink": "/articles/2024/01/01/1609459200000.html",
            "articlePutTop": true,
            "articleSignId": "1",
            "articleImg1URL": "https://b3logfile.com/bing/20171226.jpg?imageView2/1/w/1280/h/720",
            "articleStatus": 0,
            "authorName": "admin",
            "articleCreateTime": 1609459200000,
            "articleUpdateTime": 1609462800000
        },
        {
            "oId": "1609372800000",
            "articleTitle": "Docker 容器化实践",
            "articleAbstract": "",
            "articleAbstractText": "本文介绍 Docker 在实际项目中的使用经验...",
            "articleTags": "Docker,DevOps",
            "articlePermalink": "/articles/2024/01/02/1609372800000.html",
            "articlePutTop": false,
            "articleSignId": "1",
            "articleImg1URL": "https://b3logfile.com/bing/20171105.jpg?imageView2/1/w/1280/h/720",
            "articleStatus": 0,
            "authorName": "admin",
            "articleCreateTime": 1609372800000,
            "articleUpdateTime": 1609376400000
        }
    ]
}
```

**字段说明（实际返回 13 个字段）：**
- `articleTitle`: 文章标题（经过 XML 转义）
- `articleAbstract` / `articleAbstractText`: Markdown 摘要与纯文本摘要
- `articleTags`: 英文逗号分隔的标签字符串
- `articlePermalink`: 文章永久路径
- `articleImg1URL`: 文章首图 URL
- `articleSignId`: 签名档 ID
- `authorName`: 作者用户名
- `articleCreateTime` / `articleUpdateTime`: 创建与更新 Unix 毫秒时间戳
- `articlePutTop`: 是否置顶
- `articleStatus`: `0`=已发布, `1`=草稿
- 注意：**不包含** `articleViewCount` 与 `articleContent`

---

### 获取文章详情 — `GET /console/article/{id}`

返回包裹在顶层 `"article"` 对象内：

```json
{
    "code": 0,
    "article": {
        "oId": "1609459200000",
        "articleTitle": "Docker 容器化实践",
        "articleAbstract": "本文介绍 Docker 在实际项目中的使用经验...",
        "articleAbstractText": "本文介绍 Docker 在实际项目中的使用经验...",
        "articleContent": "# Docker 容器化实践\n\n## 1. 基础概念\n\nDocker 是一个...",
        "articlePermalink": "/articles/2024/01/01/1609459200000.html",
        "articleCreated": 1609459200000,
        "articleImg1URL": "https://b3logfile.com/bing/20171105.jpg?imageView2/1/w/1280/h/720",
        "articleStatus": 0,
        "articleViewPwd": "",
        "articleTags": [
            {"oId": "tag001", "tagTitle": "Docker"},
            {"oId": "tag002", "tagTitle": "DevOps"}
        ],
        "articleSignId": "1",
        "signs": [
            {"oId": "0", "signHTML": ""},
            {"oId": "1", "signHTML": "<hr/>"},
            {"oId": "2", "signHTML": ""}
        ]
    }
}
```

> **注意**：详情中的 `article.articleTags` 是对象数组；调用 `PUT /console/article/` 更新文章时，需将其转换为英文逗号分隔字符串（如 `"Docker,DevOps"`），同时保留无需修改的摘要、签名档、永久路径等字段。

---

### 创建文章 — `POST /console/article/`

**请求体：**
```json
{
    "article": {
        "articleTitle": "新文章标题",
        "articleAbstract": "摘要内容",
        "articleContent": "# 正文\n\nMarkdown 内容...",
        "articleTags": "Java,Solo",
        "articlePermalink": "",
        "articleStatus": 0,
        "postToCommunity": false,
        "articleSignId": "1",
        "articleViewPwd": ""
    }
}
```

**成功响应：**
```json
{
    "code": 0,
    "oId": "1700000000000",
    "msg": "添加成功"
}
```

**失败响应（示例）：**
```json
{
    "code": -1,
    "msg": "标题不能为空"
}
```

---

### 更新文章 — `PUT /console/article/`

**请求体：**
```json
{
    "article": {
        "oId": "1609459200000",
        "articleTitle": "更新后的标题",
        "articleAbstract": "更新后的摘要",
        "articleContent": "# 更新后的内容\n\n...",
        "articleTags": "Docker,K8s",
        "articleStatus": 0,
        "postToCommunity": false
    }
}
```

**成功响应：**
```json
{
    "code": 0,
    "msg": "更新成功"
}
```

**权限不足：**
```json
{
    "code": -1,
    "msg": "无权限"
}
```

---

### 删除文章 — `DELETE /console/article/{id}`

**成功：**
```json
{
    "code": 0,
    "msg": "删除成功"
}
```

**失败：**
```json
{
    "code": -1,
    "msg": "删除失败"
}
```

---

### 置顶文章 — `PUT /console/article/puttop/{id}`

```json
{
    "code": 0,
    "msg": "置顶成功"
}
```

---

### 取消置顶 — `PUT /console/article/canceltop/{id}`

```json
{
    "code": 0,
    "msg": "取消置顶成功"
}
```

---

### 取消发布 — `PUT /console/article/unpublish/{id}`

```json
{
    "code": 0,
    "msg": "取消发布成功"
}
```

---

## 分类管理

### 列出分类 — `GET /console/categories/{page}/{pageSize}/{windowSize}`

```json
{
    "code": 0,
    "pagination": {
        "paginationPageCount": 1,
        "paginationPageNums": [1]
    },
    "categories": [
        {
            "oId": "cat001",
            "categoryTitle": "技术笔记",
            "categoryURI": "tech-notes",
            "categoryDescription": "技术相关文章分类"
        },
        {
            "oId": "cat002",
            "categoryTitle": "生活随笔",
            "categoryURI": "life",
            "categoryDescription": ""
        }
    ]
}
```

---

### 获取分类详情 — `GET /console/category/{id}`

```json
{
    "code": 0,
    "category": {
        "oId": "cat001",
        "categoryTitle": "技术笔记",
        "categoryURI": "tech-notes",
        "categoryDescription": "技术相关文章分类"
    },
    "categoryTags": "Java,Docker,Go"
}
```

> **注意**: `categoryTags` 是逗号分隔的字符串（从标签列表拼接而来）。

---

### 创建分类 — `POST /console/category/`

**请求体：**
```json
{
    "categoryTitle": "开源项目",
    "categoryURI": "open-source",
    "categoryDescription": "开源项目介绍与实践",
    "categoryTags": "Java,Go"
}
```

**成功响应：**
```json
{
    "code": 0,
    "oId": "cat003",
    "msg": "添加成功"
}
```

**标签不存在错误：**
```json
{
    "code": -1,
    "msg": "请先发布使用标签 [Rust] 的文章"
}
```

**分类名重复：**
```json
{
    "code": -1,
    "msg": "分类名称已存在"
}
```

**URI 不合法：**
```json
{
    "code": -1,
    "msg": "分类路径必须是 ASCII 字符"
}
```

---

### 更新分类 — `PUT /console/category/`

```json
{
    "code": 0,
    "oId": "cat001",
    "msg": "更新成功"
}
```

---

### 删除分类 — `DELETE /console/category/{id}`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

---

## 标签

### 获取所有标签 — `GET /console/tags`

```json
{
    "code": 0,
    "tags": [
        {"tagTitle": "Java", "oId": "tag001", "tagPublishedRefCount": 15},
        {"tagTitle": "Docker", "oId": "tag002", "tagPublishedRefCount": 8},
        {"tagTitle": "Go", "oId": "tag003", "tagPublishedRefCount": 3}
    ]
}
```

---

## 链接管理

### 列出链接 — `GET /console/links/{page}/{pageSize}/{windowSize}`

```json
{
    "code": 0,
    "pagination": {
        "paginationPageCount": 1,
        "paginationPageNums": [1]
    },
    "links": [
        {
            "oId": "link001",
            "linkTitle": "B3log 社区",
            "linkAddress": "https://ld246.com",
            "linkDescription": "B3log 开源社区"
        }
    ]
}
```

---

### 获取链接详情 — `GET /console/link/{id}`

```json
{
    "code": 0,
    "link": {
        "oId": "link001",
        "linkTitle": "B3log 社区",
        "linkAddress": "https://ld246.com",
        "linkDescription": "B3log 开源社区"
    }
}
```

---

### 创建链接 — `POST /console/link/`

**请求体：**
```json
{
    "link": {
        "linkTitle": "GitHub",
        "linkAddress": "https://github.com",
        "linkDescription": "全球最大代码托管平台",
        "linkIcon": "https://github.com/favicon.ico"
    }
}
```

**成功响应：**
```json
{
    "code": 0,
    "oId": "link002",
    "msg": "添加成功"
}
```

---

### 更新链接 — `PUT /console/link/`

**请求体：**
```json
{
    "link": {
        "oId": "link001",
        "linkTitle": "更新后的标题",
        "linkAddress": "https://new-url.com",
        "linkDescription": "更新描述",
        "linkIcon": ""
    }
}
```

**响应：**
```json
{
    "code": 0,
    "msg": "更新成功"
}
```

---

### 删除链接 — `DELETE /console/link/{id}`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

---

## 页面管理

### 列出页面 — `GET /console/pages/{page}/{pageSize}/{windowSize}`

```json
{
    "code": 0,
    "pagination": {
        "paginationPageCount": 1,
        "paginationPageNums": [1]
    },
    "pages": [
        {
            "oId": "page001",
            "pageTitle": "关于",
            "pageOrder": 0,
            "pagePermalink": "/about",
            "pageIcon": "📝"
        },
        {
            "oId": "page002",
            "pageTitle": "留言板",
            "pageOrder": 1,
            "pagePermalink": "/guestbook",
            "pageIcon": "💬"
        }
    ]
}
```

---

### 获取页面详情 — `GET /console/page/{id}`

```json
{
    "code": 0,
    "page": {
        "oId": "page001",
        "pageTitle": "关于",
        "pageOrder": 0,
        "pagePermalink": "/about",
        "pageIcon": "📝"
    },
    "msg": "获取成功"
}
```

---

### 创建页面 — `POST /console/page/`

**请求体：**
```json
{
    "page": {
        "pageTitle": "友情链接",
        "pagePermalink": "/links",
        "pageOpenTarget": "_self",
        "pageIcon": "🔗"
    }
}
```

**成功响应：**
```json
{
    "code": 0,
    "oId": "page003",
    "msg": "添加成功"
}
```

---

### 更新页面 — `PUT /console/page/`

```json
{
    "code": 0,
    "msg": "更新成功"
}
```

---

### 删除页面 — `DELETE /console/page/{id}`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

---

## 偏好设置

### 获取偏好 — `GET /console/preference/`

```json
{
    "code": 0,
    "preference": {
        "mostUsedTagDisplayCount": 20,
        "articleListDisplayCount": 20,
        "articleListPaginationWindowSize": 20,
        "externalRelevantArticlesDisplayCount": 5,
        "relevantArticlesDisplayCount": 5,
        "randomArticlesDisplayCount": 5,
        "blogTitle": "我的博客",
        "blogSubtitle": "记录技术与生活",
        "localeString": "zh_CN",
        "timeZoneId": "Asia/Shanghai",
        "skinDirName": "bianmin",
        "skins": "[{\"skinDirName\":\"bianmin\"},{\"skinDirName\":\"Jane\"}]",
        "noticeBoard": "欢迎访问！",
        "footerContent": "",
        "htmlHead": "",
        "metaKeywords": "Java,博客,技术",
        "metaDescription": "一个技术博客",
        "enableArticleUpdateHint": true,
        "signs": "[{\"oId\":\"0\",\"signHTML\":\"\"},{\"oId\":\"1\",\"signHTML\":\"\"}]",
        "allowVisitDraftViaPermalink": false,
        "version": "4.4.0",
        "articleListStyle": "titleAndAbstract",
        "feedOutputMode": "abstract",
        "feedOutputCnt": 10,
        "faviconURL": "/favicon.ico",
        "syncGitHub": false,
        "pullGitHub": false,
        "customVars": "",
        "showCodeBlockLn": true,
        "footnotes": true,
        "showToC": true,
        "autoSpace": true,
        "fixTermTypo": true,
        "chinesePunct": false,
        "inlineMathAllowDigitAfterOpenMarker": false,
        "editorMode": "sv"
    }
}
```

---

### 更新偏好 — `PUT /console/preference/`

**成功：**
```json
{
    "code": 0,
    "msg": "更新成功"
}
```

**参数校验失败：**
```json
{
    "code": -1,
    "msg": "[参数设置 - 页面大小]  请输入非负整数"
}
```

---

## 皮肤管理

### 获取皮肤 — `GET /console/skin`

```json
{
    "code": 0,
    "skin": {
        "skinDirName": "bianmin",
        "mobileSkinDirName": "bianmin",
        "skins": "[{\"skinDirName\":\"bianmin\"},{\"skinDirName\":\"Jane\"},{\"skinDirName\":\"nijigen\"},{\"skinDirName\":\"Medium\"},{\"skinDirName\":\"Starter\"},{\"skinDirName\":\"Casper\"},{\"skinDirName\":\"Pinghsu\"},{\"skinDirName\":\"9JEALD\"}]"
    }
}
```

> **注意**: `skins` 是 JSON 字符串，需 parse 后使用。

---

### 更新皮肤 — `PUT /console/skin`

**成功：**
```json
{
    "code": 0,
    "msg": "更新成功"
}
```

**失败：**
```json
{
    "code": -1,
    "msg": "更新失败"
}
```

---

## API Key 管理

可通过 Solo 后台 **工具 → API Key 管理**（`#tools/apikey`）页面创建、启停、重命名、删除密钥，并查看每个密钥的最近调用时间、调用接口、IP 与累计次数。

### 获取 API Key 列表 — `GET /console/api-key`

```json
{
    "code": 0,
    "hasKey": true,
    "apiKey": "sk-aB3c****T2uV",
    "apiKeys": [
        {
            "id": "1763445000123abcd",
            "name": "Antigravity Agent",
            "maskedKey": "sk-aB3c****T2uV",
            "enabled": true,
            "createdAt": 1763445000123,
            "lastUsedAt": 1763445123456,
            "lastUsedIp": "121.43.102.123",
            "lastUsedEndpoint": "GET /console/tags",
            "callCount": 5
        }
    ]
}
```

> **注意**: 列表只返回脱敏后的 `maskedKey` 与统计字段，绝不回传完整明文密钥；顶层 `hasKey` / `apiKey` 为兼容字段。

---

### 创建 API Key — `POST /console/api-key`

请求体可选：`{"name": "Antigravity Agent"}`（留空则默认 `"API Key"`）。

```json
{
    "code": 0,
    "id": "1763445000123abcd",
    "name": "Antigravity Agent",
    "apiKey": "sk-aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX",
    "maskedKey": "sk-aB3c****V3wX",
    "createdAt": 1763445000123,
    "msg": "添加成功"
}
```

> **注意**: 完整明文 `apiKey` 仅在创建响应中返回一次。

---

### 更新 API Key（启停 / 重命名）— `PUT /console/api-key/{id}`

请求体：`{"enabled": false, "name": "New Name"}`（字段按需传递）。

```json
{
    "code": 0,
    "msg": "更新成功"
}
```

---

### 删除 API Key — `DELETE /console/api-key/{id}`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

---

## 其他

### 清理未使用的标签 — `DELETE /console/tag/unused`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

### 清理未使用的归档 — `DELETE /console/archive/unused`

```json
{
    "code": 0,
    "msg": "删除成功"
}
```

### 导出 JSON — `GET /console/export/json`

返回 `application/zip` 二进制内容，不是 JSON。用 `curl -o` 保存到文件。

### 导出 Hexo — `GET /console/export/hexo`

返回 `application/zip` 二进制内容，不是 JSON。用 `curl -o` 保存到文件。

---

## 文章缩略图 — `GET /console/thumbs?n=6&w=960&h=540`

```json
{
    "code": 0,
    "data": [
        "https://b3logfile.com/bing/20171226.jpg?imageView2/1/w/960/h/540/interlace/1/q/100",
        "https://b3logfile.com/bing/20171105.jpg?imageView2/1/w/960/h/540/interlace/1/q/100",
        "https://b3logfile.com/bing/20180105.jpg?imageView2/1/w/960/h/540/interlace/1/q/100",
        "https://b3logfile.com/bing/20171114.jpg?imageView2/1/w/960/h/540/interlace/1/q/100"
    ]
}
```
