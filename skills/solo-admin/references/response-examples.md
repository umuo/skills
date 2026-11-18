# Solo API 返回值示例

本文档提供 Solo 博客各 API 接口的返回值示例，从源码注释中提取。

---

## 通用结构

所有 API 返回 JSON 对象，包含 `code` 字段：

```json
// 成功
{ "code": 0, "msg": "操作成功" }

// 失败
{ "code": -1, "msg": "错误描述" }
```

---

## 文章管理

### 列出文章 — `GET /console/articles/status/{status}/{page}/{pageSize}/{windowSize}`

按文章更新日期和置顶排序。列表中**不包含**文章正文（`articleContent`）。

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
            "articleCreateTime": 1609459200000,
            "articleViewCount": 128,
            "articleTags": "年度总结,技术",
            "articlePutTop": true,
            "articleStatus": 0
        },
        {
            "oId": "1609372800000",
            "articleTitle": "Docker 容器化实践",
            "articleCreateTime": 1609372800000,
            "articleViewCount": 56,
            "articleTags": "Docker,DevOps",
            "articlePutTop": false,
            "articleStatus": 0
        }
    ]
}
```

**字段说明：**
- `articleCreateTime`: Unix 毫秒时间戳
- `articlePutTop`: 是否置顶
- `articleStatus`: 0=已发布, 1=草稿

---

### 获取文章详情 — `GET /console/article/{id}`

```json
{
    "code": 0,
    "oId": "1609459200000",
    "articleTitle": "Docker 容器化实践",
    "articleAbstract": "本文介绍 Docker 在实际项目中的使用经验...",
    "articleContent": "# Docker 容器化实践\n\n## 1. 基础概念\n\nDocker 是一个...",
    "articlePermalink": "/articles/2024/01/01/1609459200000.html",
    "articleTags": [
        {"oId": "tag001", "tagTitle": "Docker"},
        {"oId": "tag002", "tagTitle": "DevOps"}
    ],
    "articleSignId": "1",
    "signs": [
        {"oId": "1", "signHTML": ""},
        {"oId": "2", "signHTML": "<hr/>"},
        {"oId": "3", "signHTML": ""}
    ]
}
```

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

### 获取 API Key — `GET /console/api-key`

```json
{
    "code": 0,
    "apiKey": "abcd****wxyz"
}
```

> **注意**: 返回值中 API Key 中间部分会被隐藏（mask 处理）。

---

### 生成 API Key — `POST /console/api-key`

```json
{
    "code": 0,
    "apiKey": "aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2u",
    "msg": "生成成功"
}
```

---

### 删除 API Key — `DELETE /console/api-key`

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

## 文章缩略图 — `GET /console/article/thumbs?n=6&w=960&h=540`

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
