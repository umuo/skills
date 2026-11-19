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

Manage **Solo** blog (`blog.lacknb.cn`) through its Console REST API.

> [!IMPORTANT]
> Always use the bundled helper [scripts/solo_api.py](scripts/solo_api.py) when available.
> It deterministically loads `.env`, validates `sk-` keys, avoids shell quoting conflicts,
> and catches `HTTP 401` HTML error pages instead of masking them as JSON parse errors.

---

## Configuration & Credential Loading

```env
SOLO_BASE_URL=https://blog.lacknb.cn
SOLO_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Lookup Priority (Do NOT Ask the User Prematurely)

Default shell sessions do **not** inject `SOLO_API_KEY` automatically — the active key
usually lives in `.env` inside the skill directory. Resolve credentials in this exact order:

1. **Process environment**: `SOLO_API_KEY` / `SOLO_BASE_URL` (ignore empty or placeholder values like `your-api-key-here`, `sk-xxxx...`).
2. **Sibling `.env` next to this `SKILL.md`**: `<skill-dir>/.env`.
3. **Fixed agent skill paths** (check these exact paths only; **never** run recursive wildcards like `~/.*/**/solo-admin/.env` or `find ~` because hidden cache folders make them hang):
   - `~/.gemini/config/skills/solo-admin/.env`
   - `~/.codex/skills/solo-admin/.env`
   - `~/.claude/skills/solo-admin/.env`
   - `~/.agents/skills/solo-admin/.env`
4. **Prompt the user** only when no valid key is found across all locations above, or when every found key fails with `HTTP 401`.

### Multi-Key (`sk-`) Format & Legacy Key Pitfalls

- Solo 4.4+ uses **multi-API-Key** storage (`sk-...`, 35 chars total). Legacy 32-char keys without the `sk-` prefix become invalid (`401`) once the admin switches to or cleans up multi-key storage.
- **Never assume a non-empty `SOLO_API_KEY` is valid without testing.** Run `--check` first, or verify the HTTP status code on the first request.
- **Never print plaintext secrets** (`cat .env`, `echo $SOLO_API_KEY`, or pasting full keys in replies). Only show masked values (`sk-aB3c****T2uV`).

---

## Execution Pattern & Error Handling

### Recommended: Bundled Wrapper (`scripts/solo_api.py`)

```bash
SKILL_DIR="<path-to-solo-admin>"

# 1. Verify credential source, key format, and connectivity
python3 "$SKILL_DIR/scripts/solo_api.py" --check

# 2. Read endpoints
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/articles/status/published/1/10/20"

# 3. Write endpoints with multi-line Markdown/quotes (use --stdin <<'JSON' or --data-file)
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/article/" --stdin <<'JSON'
{
  "article": {
    "articleTitle": "文章标题",
    "articleContent": "# 正文\n\n含 \"双引号\"、'单引号' 与 `代码` 的内容",
    "articleTags": "标签1,标签2",
    "articleStatus": 0,
    "postToCommunity": false
  }
}
JSON

# 4. Binary zip export (refuses to overwrite target if server returns 401 HTML)
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/export/json" --output ./solo-export.zip
```

### Fallback: Native `curl` (If Running Manually)

Load `.env` via `source`, capture HTTP status separately, and parse with a quoted heredoc:

```bash
set -a; source "<skill-dir>/.env"; set +a
resp=$(curl -sS -w "\n%{http_code}" -H "X-Solo-API-Key: ${SOLO_API_KEY}" "${SOLO_BASE_URL:-https://blog.lacknb.cn}/console/tags")
http_code="${resp##*$'\n'}"
body="${resp%$'\n'*}"
[ "$http_code" = "200" ] || { echo "HTTP $http_code: $(printf '%s' "$body" | head -c 200)" >&2; exit 1; }
printf '%s' "$body" | python3 - <<'PY'
import json, sys
print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))
PY
```

> [!CAUTION]
> - **Never pipe `curl -s ... | python3 -m json.tool` directly**: on `401`/`403`, Solo returns an **HTML** error page (`401 Unauthorized!`), causing `Expecting value` and hiding the real HTTP status code.
> - **Never embed `\"` inside `python3 -c '...'` f-strings**: shell single-quote boundaries do not interpret escapes cleanly and cause syntax errors.

### Two-Layer Response Contract

| Layer | HTTP Status | Body Format | Meaning |
| --- | --- | --- | --- |
| Auth / Proxy Middleware | `401` / `403` / `404` / `5xx` | **HTML** (e.g. `401 Unauthorized!`) | Missing, disabled, deleted, or legacy invalid API key; or wrong URL/permission |
| Application Business | `200` | **JSON** `{"code": 0, ...}` | `code == 0` succeeds; non-zero (`-1`) indicates validation/business error in `msg` |
| Archive Export | `200` | **Binary** `application/zip` | Only for `/console/export/json` and `/console/export/hexo` |

Detailed response payloads for every endpoint are documented in [references/response-examples.md](references/response-examples.md).

---

## Article Management

All endpoints below require `X-Solo-API-Key: sk-...`. Replace paths below with `solo_api.py <METHOD> "<PATH>"`.

> [!IMPORTANT]
> **Before writing or publishing an article**, read [references/article-style.md](references/article-style.md) for the article writing and cover-image guidelines:
> - **Cover first when image generation is available**: Use the hand-drawn infographic prompt in the article style guide to generate 1 landscape cover image summarizing the **whole article**. Upload it via `solo_api.py --upload <file>` (or `--upload-url <url>`) to get an HTTPS URL (`<= 255` chars), and place `![文章封面](https://...)` on line 1 of `articleContent`.
> - **Skip gracefully when unavailable**: If no image-generation skill/tool is available, or image upload fails/is unconfigured, omit the cover image and publish normally — never insert local file paths or Base64 strings.

### List Articles

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/articles/status/published/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/articles/status/draft/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/articles/status/published/1/10/20?k=keyword"
```

**Actual fields per item in `articles[]`**: `oId`, `articleTitle` (XML-escaped), `articleAbstract`, `articleAbstractText`, `articleTags` (comma-separated string), `articlePermalink`, `articlePutTop`, `articleSignId`, `articleImg1URL`, `articleStatus` (`0`=published, `1`=draft), `authorName`, `articleCreateTime`, `articleUpdateTime`.

> [!NOTE]
> `articleViewCount` is **not** returned by `/console/articles/status/...` (Solo 4.4+ does not expose view counts here, so reading it yields `null`), and full `articleContent` is excluded from the list response.

### Get Article Detail

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/article/{articleId}"
```

**Response**: Wrapped under a top-level `"article"` object (`{"code": 0, "article": {...}}`).
Note the type difference: `article.articleTags` in detail responses is an **array of tag objects** (`[{"oId": "...", "tagTitle": "..."}]`), whereas create/update expects a **comma-separated string**.

### Create & Update Article

```bash
# Optional: upload local cover image (or re-host temp URL) before creating article
python3 "$SKILL_DIR/scripts/solo_api.py" --upload "/path/to/cover.png"
# python3 "$SKILL_DIR/scripts/solo_api.py" --upload-url "https://example.com/temp-cover.png"

# Create (POST /console/article/)
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/article/" --stdin <<'JSON'
{
  "article": {
    "articleTitle": "文章标题",
    "articleContent": "![文章封面](https://...)\n\n## 引言\n\nMarkdown 内容...",
    "articleAbstract": "摘要（可选，不填自动截取）",
    "articleTags": "标签1,标签2",
    "articlePermalink": "",
    "articleStatus": 0,
    "articleSignId": "1",
    "articleViewPwd": "",
    "postToCommunity": false
  }
}
JSON

# Update (PUT /console/article/) — GET detail first and preserve untouched fields!
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/article/" --stdin <<'JSON'
{
  "article": {
    "oId": "article-id-here",
    "articleTitle": "更新的标题",
    "articleContent": "更新的内容...",
    "articleAbstract": "保留或更新的摘要",
    "articleTags": "标签1,标签2",
    "articlePermalink": "/articles/...",
    "articleStatus": 0,
    "articleSignId": "1",
    "articleViewPwd": "",
    "postToCommunity": false
  }
}
JSON
```

- `articleStatus`: `0` = published, `1` = draft.
- `articleTags`: comma-separated string (at most 4 tags are kept; blank defaults to `"待分类"`). Convert `articleTags[].tagTitle` back to `"t1,t2"` before `PUT`.
- **Preserve fields on `PUT`**: Always `GET /console/article/{id}` before updating and carry over `articleAbstract`, `articlePermalink`, `articleSignId`, `articleViewPwd`, and `articleTags` unless intentionally changing them.

### Delete / Top / Unpublish / Thumbs

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" DELETE "/console/article/{articleId}"
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/article/puttop/{articleId}"
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/article/canceltop/{articleId}"
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/article/unpublish/{articleId}"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/thumbs?n=6&w=960&h=540"
```

> [!CAUTION]
> Always show the article title and confirm with the user before deleting an article.

---

## Category & Tag Management

```bash
# Categories
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/categories/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/category/{categoryId}"
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/category/" --stdin <<'JSON'
{
  "categoryTitle": "分类名",
  "categoryURI": "category-uri",
  "categoryDescription": "描述",
  "categoryTags": "tag1,tag2"
}
JSON
# PUT /console/category/ uses the same fields plus "oId"
python3 "$SKILL_DIR/scripts/solo_api.py" DELETE "/console/category/{categoryId}"

# Tags
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/tags"
python3 "$SKILL_DIR/scripts/solo_api.py" DELETE "/console/tag/unused"
```

> [!NOTE]
> `categoryURI` must be ASCII-only, and every tag listed in `categoryTags` must already exist on at least one article.

---

## Link Management

Request bodies for `POST` and `PUT` **must** wrap fields inside `"link": {...}`:

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/links/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/link/{linkId}"

# Add Link (POST /console/link/)
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/link/" --stdin <<'JSON'
{
  "link": {
    "linkTitle": "链接名称",
    "linkAddress": "https://example.com",
    "linkDescription": "描述",
    "linkIcon": "https://example.com/favicon.ico"
  }
}
JSON

# Update Link (PUT /console/link/) — include "oId" inside "link"
# Delete Link: DELETE /console/link/{linkId}
```

---

## Page Management (Navigation Links)

Solo's `page` entity represents a **navigation bar link** (there is **no `pageContent` field**). Request bodies for `POST` and `PUT` **must** wrap fields inside `"page": {...}`. To create a standalone Markdown page (such as `/about`), first create a published article with that custom `articlePermalink`, then add a navigation page pointing to it if needed.

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/pages/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/page/{pageId}"

# Add Page (POST /console/page/)
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/page/" --stdin <<'JSON'
{
  "page": {
    "pageTitle": "页面标题",
    "pagePermalink": "/custom-page",
    "pageOpenTarget": "_self",
    "pageIcon": "📄"
  }
}
JSON

# Update Page (PUT /console/page/) — include "oId" inside "page"
# Delete Page: DELETE /console/page/{pageId}
```

---

## Preferences, Skins & API Keys

### Preferences (`GET` / `PUT /console/preference/`)

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/preference/"
```

> [!WARNING]
> Always `GET /console/preference/` first, merge your updates into the existing `preference` object, and `PUT` the full merged object (including numeric display counts) to avoid overwriting fields or failing server validation.

### Skins (`GET` / `PUT /console/skin`)

```bash
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/skin"
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/skin" --data '{"skin":{"skinDirName":"Jane","mobileSkinDirName":"Jane"}}'
```

Available skin directory names can be parsed from the `skin.skins` JSON string returned by `GET /console/skin`.

### API Key Management (`/console/api-key`)

Managed in Solo Web Admin under **后台 → 工具 → API Key 管理** (`#tools/apikey`) or via REST:

```bash
# List masked keys and usage metrics
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/api-key"

# Create new key (plaintext sk-... is returned ONLY ONCE in POST response)
python3 "$SKILL_DIR/scripts/solo_api.py" POST "/console/api-key" --data '{"name": "Antigravity Agent"}'

# Enable / disable / rename
python3 "$SKILL_DIR/scripts/solo_api.py" PUT "/console/api-key/{id}" --data '{"name": "Codex Agent", "enabled": true}'

# Remove by id (DELETE /console/api-key?id={id} also works)
python3 "$SKILL_DIR/scripts/solo_api.py" DELETE "/console/api-key/{id}"
```

---

## Export, Logs & Users

```bash
# Export blog backup (.zip)
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/export/json" --output solo-export.zip
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/export/hexo" --output solo-hexo.zip

# Maintenance & logs
python3 "$SKILL_DIR/scripts/solo_api.py" DELETE "/console/archive/unused"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/log"

# Users
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/users/1/10/20"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/user/{userId}"
python3 "$SKILL_DIR/scripts/solo_api.py" GET "/console/changeRole/{userId}"
```

---

## Usage Guidelines

1. **Preflight credentials**: Run `solo_api.py --check` first; never trust an untested `.env` variable or skip checking fixed skill `.env` paths.
2. **Article style & cover image**: Read [references/article-style.md](references/article-style.md) before drafting; prefer generating a whole-article cover image via available image-gen tools and uploading via `--upload`, or omit the cover image cleanly if no image-gen/upload capability is available.
3. **Avoid duplicate content**: List existing articles and tags before creating new ones.
4. **Preserve fields on update**: For both `PUT /console/article/` and `PUT /console/preference/`, fetch the current object first and merge changes (`articleTags` -> comma string for articles).
5. **Confirm destructive ops**: Show exact title/ID and ask user confirmation before `DELETE` requests.
6. **Handle two-layer errors properly**: Report `HTTP 401`/`403` HTML errors as authentication/permission issues rather than JSON parsing bugs; report JSON `code != 0` with `msg`.
7. **Pagination**: URL pattern is `/{page}/{pageSize}/{windowSize}` — start with `1/10/20`.
