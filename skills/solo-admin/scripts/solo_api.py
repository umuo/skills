#!/usr/bin/env python3
"""Zero-dependency Solo Console API helper wrapping curl with safe credential loading."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_BASE_URL = "https://blog.lacknb.cn"

FIXED_ENV_CANDIDATES = (
    Path.home() / ".gemini" / "config" / "skills" / "solo-admin" / ".env",
    Path.home() / ".codex" / "skills" / "solo-admin" / ".env",
    Path.home() / ".claude" / "skills" / "solo-admin" / ".env",
    Path.home() / ".agents" / "skills" / "solo-admin" / ".env",
)

PLACEHOLDER_VALUES = {
    "",
    "your-api-key-here",
    "replace-with-runtime-secret",
    "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
}


@dataclass
class CredentialCandidate:
    source: str
    api_key: str
    base_url: str


def mask_key(key: str) -> str:
    """Mask an API key matching Solo's server masking convention."""
    if not key:
        return ""
    if len(key) > 11:
        return f"{key[:7]}****{key[-4:]}"
    return "****"


def is_placeholder_key(value: str) -> bool:
    """Return True if value is empty or an example placeholder."""
    cleaned = value.strip()
    if not cleaned or cleaned in PLACEHOLDER_VALUES:
        return True
    if cleaned.startswith("<") and cleaned.endswith(">"):
        return True
    if re.fullmatch(r"sk-[xX*]+", cleaned):
        return True
    return False


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE pairs from a .env file without shell execution."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
            val = val[1:-1]
        values[key] = val
    return values


def normalize_base_url(url: str) -> str:
    """Normalize Solo base URL by stripping trailing slashes."""
    cleaned = (url or "").strip().rstrip("/")
    return cleaned or DEFAULT_BASE_URL


def resolve_credentials(
    cli_base_url: Optional[str] = None,
    cli_env_file: Optional[str] = None,
) -> tuple[Optional[CredentialCandidate], str, list[str]]:
    """
    Resolve SOLO_API_KEY and SOLO_BASE_URL deterministically.

    Returns (selected_candidate, resolved_base_url, warnings).
    """
    warnings: list[str] = []
    candidates: list[CredentialCandidate] = []
    fallback_base_url = ""

    env_key = os.environ.get("SOLO_API_KEY", "").strip()
    env_base = os.environ.get("SOLO_BASE_URL", "").strip()
    if env_base:
        fallback_base_url = env_base
    if not is_placeholder_key(env_key):
        candidates.append(
            CredentialCandidate(
                source="process environment",
                api_key=env_key,
                base_url=env_base,
            )
        )

    if cli_env_file:
        env_paths = [Path(cli_env_file).expanduser()]
    else:
        skill_env = Path(__file__).resolve().parent.parent / ".env"
        seen: set[Path] = set()
        env_paths = []
        for path in [skill_env, *FIXED_ENV_CANDIDATES]:
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if resolved not in seen:
                seen.add(resolved)
                env_paths.append(path)

    for path in env_paths:
        if not path.is_file():
            continue
        parsed = parse_env_file(path)
        file_base = parsed.get("SOLO_BASE_URL", "").strip()
        if file_base and not fallback_base_url:
            fallback_base_url = file_base
        file_key = parsed.get("SOLO_API_KEY", "").strip()
        if not is_placeholder_key(file_key):
            candidates.append(
                CredentialCandidate(
                    source=str(path),
                    api_key=file_key,
                    base_url=file_base,
                )
            )

    if not candidates:
        resolved_base = normalize_base_url(cli_base_url or fallback_base_url or DEFAULT_BASE_URL)
        return None, resolved_base, warnings

    # Prefer modern sk- multi-key format if an earlier location only has a legacy unprefixed key.
    sk_candidates = [c for c in candidates if c.api_key.startswith("sk-")]
    if sk_candidates:
        chosen = sk_candidates[0]
        if candidates[0] is not chosen and not candidates[0].api_key.startswith("sk-"):
            warnings.append(
                f"Skipped legacy non-'sk-' key in {candidates[0].source} ({mask_key(candidates[0].api_key)}); "
                f"using 'sk-' key from {chosen.source} ({mask_key(chosen.api_key)})."
            )
    else:
        chosen = candidates[0]
        warnings.append(
            f"API key from {chosen.source} ({mask_key(chosen.api_key)}) does not start with 'sk-'. "
            "It may be a legacy single-key remnant that fails with HTTP 401 after multi-key migration."
        )

    resolved_base = normalize_base_url(cli_base_url or chosen.base_url or fallback_base_url or DEFAULT_BASE_URL)
    return chosen, resolved_base, warnings


def build_url(base_url: str, api_path: str) -> str:
    """Join base URL and endpoint path cleanly."""
    if api_path.startswith("http://") or api_path.startswith("https://"):
        return api_path
    normalized_path = api_path if api_path.startswith("/") else f"/{api_path}"
    return f"{base_url}{normalized_path}"


def read_request_body(args: argparse.Namespace) -> Optional[bytes]:
    """Read and validate JSON payload from --data, --data-file, or --stdin."""
    raw_text: Optional[str] = None
    if args.data is not None:
        raw_text = args.data
    elif args.data_file is not None:
        raw_text = Path(args.data_file).expanduser().read_text(encoding="utf-8")
    elif args.stdin:
        raw_text = sys.stdin.read()

    if raw_text is None:
        return None

    try:
        json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"Error: request body is not valid JSON ({exc}).", file=sys.stderr)
        sys.exit(4)

    return raw_text.encode("utf-8")


def summarize_snippet(raw_bytes: bytes, limit: int = 200) -> str:
    """Return a single-line bounded preview of non-JSON response text."""
    text = raw_bytes.decode("utf-8", errors="replace").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > limit:
        return f"{text[:limit]}..."
    return text or "<empty response>"


def run_curl(
    method: str,
    url: str,
    api_key: str,
    payload: Optional[bytes],
    body_path: Path,
) -> tuple[int, str]:
    """Invoke curl and return (http_status, content_type)."""
    curl_bin = shutil.which("curl")
    if not curl_bin:
        raise RuntimeError("curl executable not found in PATH")

    cmd = [
        curl_bin,
        "-sS",
        "-X",
        method.upper(),
        "-H",
        f"X-Solo-API-Key: {api_key}",
        "-H",
        "Content-Type: application/json",
        "-o",
        str(body_path),
        "-w",
        "%{http_code}\t%{content_type}",
        url,
    ]

    payload_tmp: Optional[Path] = None
    try:
        if payload is not None:
            fd, payload_tmp_name = tempfile.mkstemp(prefix="solo_req_", suffix=".json")
            os.close(fd)
            payload_tmp = Path(payload_tmp_name)
            payload_tmp.write_bytes(payload)
            cmd.extend(["--data-binary", f"@{payload_tmp}"])

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            err_msg = proc.stderr.strip() or f"curl exited with status {proc.returncode}"
            raise RuntimeError(err_msg)

        meta = proc.stdout.strip()
        if "\t" in meta:
            code_str, content_type = meta.split("\t", 1)
        else:
            code_str, content_type = meta, ""
        http_code = int(code_str) if code_str.isdigit() else 0
        return http_code, content_type.strip()
    finally:
        if payload_tmp and payload_tmp.exists():
            payload_tmp.unlink(missing_ok=True)


def handle_error_response(
    http_code: int,
    content_type: str,
    raw_bytes: bytes,
    cred: CredentialCandidate,
) -> int:
    """Format diagnostic error output for HTTP >= 400 responses and return exit code."""
    masked = mask_key(cred.api_key)
    snippet = summarize_snippet(raw_bytes)

    if http_code == 401:
        kind = "HTML error page instead of JSON" if "html" in (content_type or "").lower() or snippet.lstrip().startswith("<") else f"'{content_type or 'unknown'}'"
        print(
            f"Error: HTTP 401 Unauthorized (server returned {kind}: {snippet}).\n"
            f"Credential source: {cred.source} ({masked}).\n"
            "The API key may be expired, disabled, or an unmigrated legacy key. "
            "Check other fixed .env paths or generate a new 'sk-...' key in Solo Admin (#tools/apikey).",
            file=sys.stderr,
        )
        return 3

    if http_code == 403:
        print(
            f"Error: HTTP 403 Forbidden (content-type: {content_type or 'unknown'}; source: {cred.source}, {masked}).\n"
            f"Response preview: {snippet}",
            file=sys.stderr,
        )
        return 3

    print(
        f"Error: HTTP {http_code} (content-type: {content_type or 'unknown'}).\n"
        f"Response preview: {snippet}",
        file=sys.stderr,
    )
    return 4


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Call Solo Blog Console REST API safely via curl.",
    )
    parser.add_argument("method", nargs="?", help="HTTP method (GET, POST, PUT, DELETE)")
    parser.add_argument("path", nargs="?", help="Console API path, e.g. /console/articles/status/published/1/10/20")
    body_group = parser.add_mutually_exclusive_group()
    body_group.add_argument("--data", help="Inline JSON request body")
    body_group.add_argument("--data-file", help="Path to a JSON file for request body")
    body_group.add_argument("--stdin", action="store_true", help="Read JSON request body from stdin")
    parser.add_argument("--output", help="Save binary response (e.g. export zip) to this file path")
    parser.add_argument("--base-url", help="Override SOLO_BASE_URL")
    parser.add_argument("--env-file", help="Override .env lookup with a specific .env file")
    parser.add_argument("--check", action="store_true", help="Verify credential loading and test GET /console/api-key")
    args = parser.parse_args()

    if args.check:
        method = "GET"
        api_path = "/console/api-key"
    else:
        if not args.method or not args.path:
            parser.error("METHOD and PATH are required unless --check is specified.")
        method = args.method.upper()
        api_path = args.path

    cred, base_url, warnings = resolve_credentials(
        cli_base_url=args.base_url,
        cli_env_file=args.env_file,
    )
    for warn in warnings:
        print(f"Warning: {warn}", file=sys.stderr)

    if cred is None:
        checked_paths = ", ".join(str(p) for p in [Path(__file__).resolve().parent.parent / ".env", *FIXED_ENV_CANDIDATES])
        print(
            "Error: SOLO_API_KEY not found in environment or fixed skill .env locations.\n"
            f"Checked: {checked_paths}\n"
            "Ask the user for a 'sk-...' API key generated in Solo Web Admin (工具 → API Key 管理, #tools/apikey) "
            "or save it to the skill .env file.",
            file=sys.stderr,
        )
        return 2

    payload = read_request_body(args)
    url = build_url(base_url, api_path)

    fd, body_tmp_name = tempfile.mkstemp(prefix="solo_resp_")
    os.close(fd)
    body_tmp = Path(body_tmp_name)

    try:
        try:
            http_code, content_type = run_curl(method, url, cred.api_key, payload, body_tmp)
        except RuntimeError as exc:
            print(f"Error: request failed: {exc}", file=sys.stderr)
            return 4

        raw_bytes = body_tmp.read_bytes()

        if http_code >= 400 or http_code == 0:
            return handle_error_response(http_code, content_type, raw_bytes, cred)

        if args.output:
            lowered_ct = content_type.lower()
            trimmed_head = raw_bytes[:64].lstrip().lower()
            if "text/html" in lowered_ct or trimmed_head.startswith(b"<!doctype") or trimmed_head.startswith(b"<html"):
                print(
                    f"Error: refused to save {args.output} because HTTP {http_code} returned HTML ({content_type}) "
                    f"instead of binary data: {summarize_snippet(raw_bytes)}",
                    file=sys.stderr,
                )
                return 4
            out_path = Path(args.output).expanduser()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(body_tmp, out_path)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "httpStatus": http_code,
                        "contentType": content_type,
                        "savedTo": str(out_path),
                        "bytes": out_path.stat().st_size,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        try:
            parsed = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            print(
                f"Error: HTTP {http_code} returned non-JSON response (content-type: {content_type or 'unknown'}).\n"
                f"Response preview: {summarize_snippet(raw_bytes)}",
                file=sys.stderr,
            )
            return 4

        if args.check:
            code_val = parsed.get("code") if isinstance(parsed, dict) else None
            keys_list = parsed.get("apiKeys", []) if isinstance(parsed, dict) else []
            enabled_count = sum(1 for item in keys_list if isinstance(item, dict) and item.get("enabled", True))
            summary = {
                "ok": code_val == 0,
                "httpStatus": http_code,
                "baseUrl": base_url,
                "credentialSource": cred.source,
                "maskedKey": mask_key(cred.api_key),
                "totalKeys": len(keys_list),
                "enabledKeys": enabled_count,
                "code": code_val,
            }
            if code_val != 0 and isinstance(parsed, dict) and "msg" in parsed:
                summary["msg"] = parsed["msg"]
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            if code_val != 0:
                print(f"Solo API returned error (code={code_val}): {parsed.get('msg', '')}", file=sys.stderr)
                return 1
            return 0

        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        if isinstance(parsed, dict) and parsed.get("code", 0) != 0:
            print(f"Solo API error (code={parsed.get('code')}): {parsed.get('msg', '')}", file=sys.stderr)
            return 1
        return 0
    finally:
        body_tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
