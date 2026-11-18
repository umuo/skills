---
name: solo-admin
description: >-
  Manage the Solo blog system (blog.lacknb.cn) via its REST API — write and publish
  articles, manage categories/tags/links/pages, change skins, and adjust preferences.
  Use this skill whenever the user says "发博客", "写文章", "管理博客", "博客设置",
  "换皮肤", "管理分类", "管理标签", "管理链接", "管理页面", "博客数据", "清理标签",
  "导出博客", "Solo", or any reference to their personal blog at blog.lacknb.cn.
  Also trigger when the user wants to publish content, draft posts, list articles,
  or perform any blog administration task. This skill directly wraps Solo's console
  REST API using curl with API Key authentication.
---

# Solo Blog Admin Skill

Manage **Solo** blog (blog.lacknb.cn) through its REST Console API.

> [!IMPORTANT]
> All API calls require the `X-Solo-API-Key` header. The API Key is stored on the
> server in Solo's option table. If you don't have the key, ask the user to generate
> one from the Solo admin panel (`POST /console/api-key`).

---

## Configuration

```
SOLO_BASE_URL=https://blog.lacknb.cn
SOLO_API_KEY=<ask user or read from env>
```

The base curl command pattern:

```bash
curl -s -H "X-Solo-API-Key: ${SOLO_API_KEY}" -H "Content-Type: application/json" "${SOLO_BASE_URL}/console/..."
```

---

## API Reference

### Authentication Header

All requests must include:
```
X-Solo-API-Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Response Format

All APIs return JSON:
```json
{
  "code": 0,     // 0 = success, non-zero = error
  "msg": "...",  // error message (on failure)
  ...            // additional data
}
```

---

## Article Management

### List Articles

```bash
# List published articles (page 1, 10 per page)
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/articles/status/published/1/10/20"

# List drafts
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/articles/status/draft/1/10/20"

# Search by keyword
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/articles/status/published/1/10/20?k=keyword"
```

**Response**: `{ "code": 0, "pagination": {...}, "articles": [{...}] }`

Each article has: `oId`, `articleTitle`, `articleCreateTime`, `articleViewCount`, `articleTags`, `articlePutTop`, `articleStatus`

### Get Article Detail

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/article/{articleId}"
```

**Response**: Full article with `articleContent`, `articleAbstract`, `articlePermalink`, etc.

### Create Article

```bash
curl -s -X POST -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/article/" -d '{
  "article": {
    "articleTitle": "文章标题",
    "articleContent": "Markdown 内容...",
    "articleAbstract": "摘要（可选，不填自动截取）",
    "articleTags": "标签1,标签2",
    "articleStatus": 0,
    "postToCommunity": false
  }
}'
```

- `articleStatus`: `0` = published, `1` = draft
- `articleTags`: comma-separated tag names
- `articlePermalink`: optional custom permalink
- `articleViewPwd`: optional view password
- `postToCommunity`: whether to push to B3log community

**Response**: `{ "code": 0, "oId": "generated-article-id" }`

### Update Article

```bash
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/article/" -d '{
  "article": {
    "oId": "article-id-here",
    "articleTitle": "更新的标题",
    "articleContent": "更新的内容...",
    "articleTags": "标签1,标签2",
    "articleStatus": 0
  }
}'
```

### Delete Article

```bash
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/article/{articleId}"
```

> [!CAUTION]
> Always confirm with the user before deleting articles. Show the article title first.

### Toggle Top / Unpublish

```bash
# Pin to top
curl -s -X PUT -H "X-Solo-API-Key: $KEY" "$BASE/console/article/puttop/{articleId}"

# Cancel top
curl -s -X PUT -H "X-Solo-API-Key: $KEY" "$BASE/console/article/canceltop/{articleId}"

# Unpublish (move to draft)
curl -s -X PUT -H "X-Solo-API-Key: $KEY" "$BASE/console/article/unpublish/{articleId}"
```

---

## Category Management

### List Categories

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/categories/1/10/20"
```

### Get Category

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/category/{categoryId}"
```

### Create Category

```bash
curl -s -X POST -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/category/" -d '{
  "categoryTitle": "分类名",
  "categoryURI": "category-uri",
  "categoryDescription": "描述",
  "categoryTags": "tag1,tag2"
}'
```

> [!NOTE]
> `categoryURI` must be ASCII only. `categoryTags` references existing tags —
> the tags must already exist (create an article with those tags first).

### Update Category

```bash
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/category/" -d '{
  "oId": "category-id",
  "categoryTitle": "新名称",
  "categoryURI": "new-uri",
  "categoryDescription": "新描述",
  "categoryTags": "tag1,tag2"
}'
```

### Delete Category

```bash
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/category/{categoryId}"
```

---

## Tag Management

### List All Tags

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/tags"
```

**Response**: `{ "code": 0, "tags": [{ "tagTitle": "...", ... }] }`

### Remove Unused Tags

```bash
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/tag/unused"
```

---

## Link Management

### List Links

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/links/1/10/20"
```

### Add Link

```bash
curl -s -X POST -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/link/" -d '{
  "linkTitle": "链接名称",
  "linkAddress": "https://example.com",
  "linkDescription": "描述",
  "linkIcon": "https://example.com/favicon.ico"
}'
```

### Update / Delete Link

```bash
# Update
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/link/" -d '{ "oId": "id", "linkTitle": "...", "linkAddress": "..." }'

# Delete
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/link/{linkId}"
```

---

## Page Management

### List Pages

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/pages/1/10/20"
```

### Add / Update / Delete Page

```bash
# Add
curl -s -X POST -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/page/" -d '{
  "pageTitle": "页面标题",
  "pageContent": "Markdown 内容",
  "pagePermalink": "/custom-page",
  "pageOpenTarget": "_self",
  "pageIcon": "📄"
}'

# Update (include oId)
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/page/" -d '{ "oId": "id", "pageTitle": "...", "pageContent": "..." }'

# Delete
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/page/{pageId}"
```

---

## Preferences & Settings

### Get Preferences

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/preference/"
```

Returns: `blogTitle`, `blogSubtitle`, `metaKeywords`, `metaDescription`, `noticeBoard`,
`localeString`, `timeZoneId`, `articleListDisplayCount`, `faviconURL`, skin settings, etc.

### Update Preferences

```bash
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/preference/" -d '{
  "preference": {
    "blogTitle": "My Blog",
    "blogSubtitle": "subtitle",
    "mostUsedTagDisplayCount": 15,
    "articleListDisplayCount": 20,
    "articleListPaginationWindowSize": 15,
    "relevantArticlesDisplayCount": 5,
    "randomArticlesDisplayCount": 5,
    "externalRelevantArticlesDisplayCount": 0,
    "feedOutputMode": "abstract",
    "feedOutputCnt": 10,
    "faviconURL": "/favicon.ico"
  }
}'
```

> [!WARNING]
> When updating preferences, GET the current preference first to avoid overwriting
> fields you don't intend to change. Merge your changes with existing values.

---

## Skin Management

### Get Current Skin

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/skin"
```

### Switch Skin

```bash
curl -s -X PUT -H "X-Solo-API-Key: $KEY" -H "Content-Type: application/json" \
  "$BASE/console/skin" -d '{
  "skin": {
    "skinDirName": "Jane",
    "mobileSkinDirName": "Jane"
  }
}'
```

Available skins (directory names): `9JEYM3GONT`, `Andrea`, `Bruce`, `Casper`, `Community`,
`Dillinger`, `favourite`, `Finding`, `i-flavor`, `Jane`, `Medium`, `mobile`,
`nijigen`, `owmx-3.0`, `timeline`, `tree-house`, `yilia`

---

## API Key Management

### Get API Key Status

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/api-key"
```

### Generate New API Key

```bash
curl -s -X POST -H "X-Solo-API-Key: $KEY" "$BASE/console/api-key"
```

> [!IMPORTANT]
> The first API Key must be generated from the Solo admin web UI (cookie auth),
> or by directly inserting into the database via SSH:
> ```sql
> INSERT INTO b3_solo_option (oId, optionCategory, optionValue)
> VALUES ('apiKey', 'api', 'sk-your-random-32-char-key-here')
> ON DUPLICATE KEY UPDATE optionValue='sk-your-random-32-char-key-here';
> ```

### Remove API Key

```bash
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/api-key"
```

---

## Export / Import

### Export as JSON

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/export/json" -o solo-export.zip
```

### Export as Hexo

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/export/hexo" -o solo-hexo.zip
```

---

## Other Operations

### Remove Unused Archives

```bash
curl -s -X DELETE -H "X-Solo-API-Key: $KEY" "$BASE/console/archive/unused"
```

### View Server Log

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/log"
```

---

## User Management

### List Users

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/users/1/10/20"
```

### Get User

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/user/{userId}"
```

### Toggle User Role

```bash
curl -s -H "X-Solo-API-Key: $KEY" "$BASE/console/changeRole/{userId}"
```

---

## Usage Guidelines

1. **Before writing**: Always check existing articles/tags to avoid duplicates
2. **Article creation**: Use Markdown format for `articleContent`
3. **Confirm destructive ops**: Always show the item to be deleted and ask for confirmation
4. **Preference updates**: GET first, then merge changes, then PUT
5. **Tag management**: Tags are created automatically when used in articles
6. **Error handling**: Check `code` field — `0` means success, anything else is an error; show `msg` to user
7. **Pagination**: URL pattern is `/{page}/{pageSize}/{windowSize}` — start with `1/10/20`
8. **API Key setup**: For first-time setup, generate via SQL insert or Solo web admin
