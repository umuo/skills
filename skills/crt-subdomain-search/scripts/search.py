#!/usr/bin/env python3
"""Query crt.name for domains and optional first-seen dates using curl."""

import argparse
from datetime import datetime, timezone
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlencode, urlsplit


def normalize_domain(value):
    value = value.strip().rstrip('.').lower()
    value = value.encode('idna').decode('ascii')
    labels = value.split('.')
    if len(value) > 253 or len(labels) < 2 or any(
        not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
        for label in labels
    ):
        raise ValueError('无效域名：' + value)
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return value
    raise ValueError('请输入域名，而不是 IP 地址')


def parse_response(body, apex, include_apex=False):
    names = set()
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        wildcard = line.startswith('*.')
        name = normalize_domain(line[2:] if wildcard else line)
        if name != apex and not name.endswith('.' + apex):
            raise ValueError('接口返回目标域名范围外的名称：' + line)
        if wildcard:
            names.add('*.' + name)
        elif include_apex or name != apex:
            names.add(name)
    return sorted(names)


def parse_dates(body, apex, include_apex=False):
    rows = json.loads(body)
    if not isinstance(rows, list):
        raise ValueError('日期响应必须是 JSON 数组')
    dates = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('sub'), str) or 'first_seen' not in row:
            raise ValueError('日期记录缺少 sub 或 first_seen')
        raw_name = row['sub'].strip()
        if not raw_name or len(raw_name.splitlines()) != 1:
            raise ValueError('日期记录中的 sub 必须是单个域名')
        names = parse_response(raw_name, apex, include_apex)
        date = row['first_seen']
        if date is not None:
            if not isinstance(date, str):
                raise ValueError('first_seen 必须是时间字符串或 null')
            stamp = datetime.fromisoformat(date.replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('first_seen 缺少时区')
        for name in names:
            previous = dates.get(name)
            if name not in dates or (date is not None and (
                previous is None or stamp < datetime.fromisoformat(previous.replace('Z', '+00:00'))
            )):
                dates[name] = date
    return dict(sorted(dates.items()))


def main():
    parser = argparse.ArgumentParser(description='通过 crt.name 查询子域名')
    parser.add_argument('domain', help='eTLD+1 根域名或其 HTTP(S) URL；不自动推断公共后缀')
    parser.add_argument('--include-apex', action='store_true', help='保留返回的根域名')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--dates', action='store_true', help='包含首次发现日期，未知日期保留为空值')
    parser.add_argument('--output', type=Path, help='保存到新文件，不覆盖已有文件')
    args = parser.parse_args()
    try:
        target = args.domain
        if '://' in target:
            parsed = urlsplit(target)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname:
                raise ValueError('URL 必须是有效的 HTTP(S) URL')
            target = parsed.hostname
        apex = normalize_domain(target)
        if args.output and args.output.exists():
            raise ValueError('输出文件已存在：' + str(args.output))
        params = {'apex': apex}
        if args.dates:
            params.update(format='json', dates='1')
        source = 'https://crt.name/v1/search?' + urlencode(params)
        response = subprocess.run(
            ['curl', '--fail-with-body', '--silent', '--show-error',
             '--connect-timeout', '10', '--max-time', '45',
             source],
            capture_output=True, timeout=50,
        )
        if response.returncode:
            raise ValueError('请求失败：' + response.stderr.decode('utf-8', errors='replace').strip())
        body = response.stdout.decode('utf-8')
        dates = parse_dates(body, apex, args.include_apex) if args.dates else None
        domains = list(dates) if dates is not None else parse_response(body, apex, args.include_apex)
        result = {
            'apex': apex,
            'queried_at': datetime.now(timezone.utc).isoformat(),
            'source': source,
            'include_apex': args.include_apex,
            'count': len(domains),
            'domains': domains,
        }
        if dates is not None:
            result['first_seen'] = dates
        text_output = ''.join(
            name + ('\t' + (dates[name] or '') if dates is not None else '') + '\n'
            for name in domains
        )
        output = (json.dumps(result, ensure_ascii=False, indent=2) + '\n'
                  if args.format == 'json' else text_output)
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(output)
            print(f'已保存 {len(domains)} 条名称到 {args.output}', file=sys.stderr)
        else:
            sys.stdout.write(output)
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
