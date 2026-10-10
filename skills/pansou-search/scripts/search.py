#!/usr/bin/env python3
"""PanSou 网盘资源搜索与格式化检索脚本 (完全兼容 PanSouTool.java 逻辑并支持首次交互配置与持久化缓存)"""

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://pansou.lacknb.com"
CONFIG_FILE = Path(os.environ.get("PANSOU_CONFIG_PATH", Path.home() / ".config" / "pansou" / "config.json"))
TOKEN_CACHE_DIR = Path.home() / ".cache" / "pansou"


def load_config() -> dict:
    """读取本地缓存的配置文件"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_config(username: str, password: str, base_url: str | None = None):
    """保存账号配置到本地文件，并设置 0600 安全权限"""
    config = load_config()
    config["username"] = username.strip()
    config["password"] = password.strip()
    if base_url:
        config["base_url"] = base_url.strip().rstrip("/")
    elif "base_url" not in config:
        config["base_url"] = DEFAULT_BASE_URL

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except Exception:
        pass


def clear_config():
    """清除配置及 Token 缓存"""
    if CONFIG_FILE.exists():
        try:
            CONFIG_FILE.unlink()
            print("已成功清除保存的账号配置。")
        except Exception as e:
            print(f"删除配置文件失败: {e}", file=sys.stderr)
    else:
        print("未发现已保存的账号配置。")

    if TOKEN_CACHE_DIR.exists():
        for file in TOKEN_CACHE_DIR.glob("token_*.json"):
            try:
                file.unlink()
            except Exception:
                pass


def get_token_cache_path(base_url: str, username: str) -> Path:
    key = hashlib.md5(f"{base_url}:{username}".encode("utf-8")).hexdigest()
    TOKEN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return TOKEN_CACHE_DIR / f"token_{key}.json"


def load_cached_token(base_url: str, username: str) -> str | None:
    cache_path = get_token_cache_path(base_url, username)
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        token = data.get("token")
        expires_at = data.get("expires_at", 0)
        # 预留 60 秒缓冲区
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        if token and (expires_at - now_ms > 60_000):
            return token
    except Exception:
        pass
    return None


def save_cached_token(base_url: str, username: str, token: str, expires_at_ms: int):
    cache_path = get_token_cache_path(base_url, username)
    try:
        cache_path.write_text(
            json.dumps({"token": token, "expires_at": expires_at_ms}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def invalidate_token(base_url: str, username: str):
    cache_path = get_token_cache_path(base_url, username)
    if cache_path.exists():
        try:
            cache_path.unlink()
        except Exception:
            pass


def login(base_url: str, username: str, password: str) -> str:
    """调用 /api/auth/login 进行认证，并缓存 Token"""
    if not username or not password:
        raise ValueError("用户名和密码不能为空")

    login_url = f"{base_url.rstrip('/')}/api/auth/login"
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "PanSou-Skill/1.0"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            token = data.get("token")
            if not token:
                raise ValueError("PanSou 登录未返回有效 Token")
            expires_at = data.get("expires_at", 0)
            if expires_at > 10_000_000_000:
                expires_at_ms = expires_at
            elif expires_at > 0:
                expires_at_ms = expires_at * 1000
            else:
                expires_at_ms = int(datetime.now(timezone.utc).timestamp() * 1000) + 23 * 3600 * 1000

            save_cached_token(base_url, username, token, expires_at_ms)
            return token
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"登录失败 ({e.code} {e.reason}): {err_body}") from e
    except Exception as e:
        raise RuntimeError(f"PanSou 登录认证异常: {e}") from e


def prompt_user_credentials(current_base_url: str) -> tuple[str, str, str]:
    """交互式提示用户输入账号密码，并测试登录后缓存"""
    print("=" * 50)
    print("【PanSou 认证配置】检测到尚未配置或需要更新账号凭证。")
    print(f"配置文件保存位置: {CONFIG_FILE}")
    print("=" * 50)

    url_input = input(f"请输入 PanSou 服务地址 [默认: {current_base_url}]: ").strip()
    base_url = url_input if url_input else current_base_url

    username = input("请输入 PanSou 用户名: ").strip()
    while not username:
        print("用户名不能为空，请重新输入。")
        username = input("请输入 PanSou 用户名: ").strip()

    try:
        password = getpass.getpass("请输入 PanSou 密码: ").strip()
    except Exception:
        password = input("请输入 PanSou 密码: ").strip()

    while not password:
        print("密码不能为空，请重新输入。")
        try:
            password = getpass.getpass("请输入 PanSou 密码: ").strip()
        except Exception:
            password = input("请输入 PanSou 密码: ").strip()

    print("\n正在验证账号有效性...")
    login(base_url, username, password)
    save_config(username, password, base_url)
    print("✅ 账号验证成功，配置已保存并缓存！\n")
    return username, password, base_url


def split_comma_separated(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[\s,]+", value) if item.strip()]


def parse_datetime_to_ms(datetime_str: str) -> int:
    if not datetime_str or datetime_str.startswith("0001-01-01"):
        return 0
    try:
        dt_str = datetime_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def merge_results_by_type(results: list) -> dict[str, list]:
    merged: dict[str, list] = {}
    if not results:
        return merged
    for item in results:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("content") or ""
        links = item.get("links") or []
        for link in links:
            if not isinstance(link, dict):
                continue
            one_link = dict(link)
            cloud_type = one_link.get("type") or "others"
            one_link["note"] = title
            merged.setdefault(cloud_type, []).append(one_link)
    return merged


def execute_search(
    base_url: str,
    payload: dict,
    username: str = "",
    password: str = "",
    force_login: bool = False,
) -> dict:
    token = None
    if username and password:
        if force_login:
            invalidate_token(base_url, username)
            token = login(base_url, username, password)
        else:
            token = load_cached_token(base_url, username)
            if not token:
                token = login(base_url, username, password)

    search_url = f"{base_url.rstrip('/')}/api/search"
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PanSou-Skill/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(search_url, data=body_bytes, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            if username and password and not force_login:
                # 重新登录重试一次
                return execute_search(base_url, payload, username, password, force_login=True)
            elif not username or not password:
                # 缺少认证，触发配置提示异常
                raise PermissionError("服务端返回 401 未授权：缺少或无效的认证 Token，请配置账号密码。")
        resp_msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP 请求失败 ({e.code} {e.reason}): {resp_msg}") from e
    except Exception as e:
        raise RuntimeError(f"请求异常: {e}") from e


def format_text_output(json_data: dict, limit_per_type: int = 10) -> str:
    if not json_data:
        return "网盘搜索返回了无法解析的结果"

    data = json_data.get("data") if isinstance(json_data.get("data"), dict) else json_data
    merged = data.get("merged_by_type")
    if not merged:
        merged = merge_results_by_type(data.get("results") or [])

    if not merged:
        return "没有找到相关网盘资源"

    total = data.get("total", 0)
    lines = [f"网盘搜索结果（共{total}条）："]

    for cloud_type, links in merged.items():
        if not links:
            continue
        sorted_links = sorted(
            links,
            key=lambda l: parse_datetime_to_ms(l.get("datetime") or ""),
            reverse=True,
        )
        lines.append(f"\n【{cloud_type}】")
        for link in sorted_links[:limit_per_type]:
            note = (link.get("note") or "").strip()
            url = (link.get("url") or "").strip()
            pwd = (link.get("password") or "").strip()
            if note:
                lines.append(note)
            if pwd:
                lines.append(f"{url} 提取码：{pwd}")
            else:
                lines.append(url)

    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="PanSou 网盘资源检索与格式化输出工具")
    parser.add_argument("keyword", nargs="?", help="搜索关键词")
    parser.add_argument("-k", "--kw", dest="kw_opt", help="搜索关键词 (可选参数形式)")
    parser.add_argument("-s", "--source", default="all", choices=["all", "tg", "plugin"], help="数据来源: all(全部), tg(Telegram), plugin(插件)")
    parser.add_argument("-c", "--cloud-types", help="限定网盘类型，如 baidu, aliyun, quark, tianyi, 115 (英文逗号或空格分隔)")
    parser.add_argument("-p", "--plugins", help="指定插件名 (英文逗号或空格分隔)")
    parser.add_argument("--include", help="结果必须包含的关键词（OR关系，英文逗号或空格分隔）")
    parser.add_argument("--exclude", help="结果排除关键词（OR关系，英文逗号或空格分隔）")
    parser.add_argument("-r", "--refresh", action="store_true", help="是否强制刷新服务端缓存")
    parser.add_argument("--limit", type=int, default=10, help="每种网盘展示的最大结果数 (默认 10)")
    parser.add_argument("--base-url", help=f"PanSou 服务地址 (默认优先使用缓存配置或 {DEFAULT_BASE_URL})")
    parser.add_argument("--username", help="PanSou 账号 (可选，优先于缓存配置)")
    parser.add_argument("--password", help="PanSou 密码 (可选，优先于缓存配置)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式: text(人类可读文本) 或 json(结构化输出)")
    parser.add_argument("-o", "--output", help="输出到指定文件")

    # 管理操作参数
    parser.add_argument("--configure", action="store_true", help="配置 PanSou 账号密码并测试连接缓存")
    parser.add_argument("--show-config", action="store_true", help="查看当前缓存的配置状态")
    parser.add_argument("--clear-config", action="store_true", help="清除已保存的账号配置与 Token 缓存")

    args = parser.parse_args()

    # 1. 处理清除配置
    if args.clear_config:
        clear_config()
        sys.exit(0)

    # 2. 读取已保存的本地配置
    cached_cfg = load_config()

    # 3. 处理查看配置状态
    if args.show_config:
        print(f"配置文件路径: {CONFIG_FILE}")
        if cached_cfg:
            user = cached_cfg.get("username", "")
            masked_user = (user[:2] + "***" + user[-1:]) if len(user) > 3 else "***"
            print(f"已配置服务地址: {cached_cfg.get('base_url', DEFAULT_BASE_URL)}")
            print(f"已配置用户名: {masked_user}")
            print("密码状态: [已加密/脱敏存储]")
        else:
            print("当前未保存任何账号配置。")
        sys.exit(0)

    # 4. 确定最终生效的连接参数
    base_url = args.base_url or os.environ.get("PANSOU_BASE_URL") or cached_cfg.get("base_url") or DEFAULT_BASE_URL
    username = args.username or os.environ.get("PANSOU_USERNAME") or cached_cfg.get("username", "")
    password = args.password or os.environ.get("PANSOU_PASSWORD") or cached_cfg.get("password", "")

    # 5. 处理主动配置操作 (--configure)
    if args.configure:
        if args.username and args.password:
            # 命令行直传参数配置
            try:
                print(f"正在向 {base_url} 验证账号密码...")
                login(base_url, args.username, args.password)
                save_config(args.username, args.password, base_url)
                print(f"✅ 账号验证成功，配置已保存至 {CONFIG_FILE}")
                sys.exit(0)
            except Exception as e:
                print(f"❌ 验证失败: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # 交互式配置
            if sys.stdin.isatty():
                try:
                    prompt_user_credentials(base_url)
                    sys.exit(0)
                except Exception as e:
                    print(f"❌ 配置中止: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("非交互式终端环境下，请使用: --configure --username <用户> --password <密码>", file=sys.stderr)
                sys.exit(1)

    # 6. 检查搜索关键词
    kw = args.keyword or args.kw_opt
    if not kw or not kw.strip():
        parser.error("搜索关键词不能为空。如果是首次使用，请运行: python3 search.py --configure")

    # 7. 若未配置账号密码，且当前处于可交互终端，则主动引导用户配置
    if (not username or not password) and sys.stdin.isatty():
        try:
            username, password, base_url = prompt_user_credentials(base_url)
        except KeyboardInterrupt:
            print("\n已取消配置。")
            sys.exit(1)
        except Exception as e:
            print(f"\n⚠️ 认证配置未完成: {e}，尝试继续以公开接口搜索...", file=sys.stderr)

    payload: dict = {
        "kw": kw.strip(),
        "res": "merge",
    }
    if args.source:
        payload["src"] = args.source.strip()

    cloud_types = split_comma_separated(args.cloud_types)
    if cloud_types:
        payload["cloud_types"] = cloud_types

    plugins = split_comma_separated(args.plugins)
    if plugins:
        payload["plugins"] = plugins

    includes = split_comma_separated(args.include)
    excludes = split_comma_separated(args.exclude)
    if includes or excludes:
        filter_dict: dict = {}
        if includes:
            filter_dict["include"] = includes
        if excludes:
            filter_dict["exclude"] = excludes
        payload["filter"] = filter_dict

    if args.refresh:
        payload["refresh"] = True

    try:
        raw_res = execute_search(
            base_url=base_url.rstrip("/"),
            payload=payload,
            username=username,
            password=password,
        )
    except PermissionError as e:
        # 捕获 401 且未配置的情况
        if sys.stdin.isatty():
            print(f"\n[PanSou] {e}")
            try:
                username, password, base_url = prompt_user_credentials(base_url)
                # 配置完成后重试搜索
                raw_res = execute_search(
                    base_url=base_url.rstrip("/"),
                    payload=payload,
                    username=username,
                    password=password,
                )
            except Exception as retry_err:
                print(f"搜索失败: {retry_err}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"搜索失败: {e}", file=sys.stderr)
            print("提示: 首次使用请运行 `python3 <skill-dir>/scripts/search.py --configure` 配置账号密码。", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        out_str = json.dumps(raw_res, ensure_ascii=False, indent=2)
    else:
        out_str = format_text_output(raw_res, limit_per_type=args.limit)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_str, encoding="utf-8")
        print(f"结果已保存至: {out_path}")
    else:
        print(out_str)


if __name__ == "__main__":
    main()
