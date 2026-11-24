#!/usr/bin/env python3
"""BabelTele compiler / decompiler / fidelity gate.

Three deterministic operations, no network, no model calls:

  compile   natural language  ->  BabelTele (logic symbols + head-morpheme abbrevs)
  decode    BabelTele         ->  readable approximation (for review, not for shipping)
  check     compare src vs compiled: entity conservation + token density

The compiler is deliberately conservative: it never invents a symbol and never
drops a protected entity (IP / URL / path / identifier / quoted string / number).
Compression that loses a parameter is worse than no compression at all.

Usage:
  python babeltele.py compile --in plan.md [--out plan.bt] [--list]
  echo "请帮我对 target 做端口扫描" | python babeltele.py compile
  python babeltele.py decode --in plan.bt
  python babeltele.py check --src plan.md --dst plan.bt [--json]
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEXICON_PATH = HERE / "lexicon.json"

# Entities that must survive byte-for-byte. Facts are not compressible.
ENTITY_PATTERNS = [
    ("url", re.compile(r"https?://[^\s，。；;、）)\]}>\"']+")),
    ("ipv4", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{1,5})?\b")),
    ("path", re.compile(r"(?<![\w.])/(?:[\w.~%-]+/)*[\w.~%-]*")),
    ("ident", re.compile(r"\b[a-z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)+\b")),
    ("camel", re.compile(r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b")),
    ("acronym", re.compile(r"\b[A-Z][A-Z0-9_]{1,}\b")),
    # bare hostnames and file names: "shop.example.com", "upload.php"
    ("domain", re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}\b")),
    # query parameter names, including single-letter ones: "?q=", "&userId="
    ("param", re.compile(r"[?&][A-Za-z_][A-Za-z0-9_-]*=?")),
    ("quoted", re.compile(r"`[^`\n]+`|\"[^\"\n]{1,80}\"")),
    ("number", re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:%|ms|s|kb|mb|gb)?\b")),
]

# Decoding only guards hard facts: acronyms and identifiers must stay reversible
# so that "IDOR read" can come back as one concept.
DECODE_GUARDS = [p for name, p in ENTITY_PATTERNS
                 if name in {"url", "ipv4", "path", "quoted", "number", "domain", "param"}]

# Filler that survives anywhere in a sentence, not just at the start.
MID_FILLER = ["帮我", "麻烦你", "麻烦您", "麻烦", "我想要", "我想", "劳驾", "请问一下", "请问"]

TREE_PREFIX = re.compile(r"^[\s>]*(?:[├└│┌┐┘┬┴┼─]+|[-*+]\s|\d+[.)]\s)")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


class Babel:
    def __init__(self, path: Path = LEXICON_PATH, level: int = 2) -> None:
        self.level = level
        raw = json.loads(path.read_text("utf-8"))
        self.decode_skip = set(raw.get("decode_skip", []))
        self.filler = sorted({f for f in raw["filler"]}, key=len, reverse=True)
        self.intent = sorted(((_norm(k), v) for k, v in raw["intent"]), key=lambda p: -len(p[0]))
        self.symbols = sorted(((_norm(k), v) for k, v in raw["symbols"]), key=lambda p: -len(p[0]))
        self.abbrev = sorted(((_norm(k), v) for k, v in raw["abbrev"]), key=lambda p: -len(p[0]))
        self.back: dict[str, str] = {}
        for key, val in raw["intent"]:
            self.back.setdefault(val, _norm(key))
        for key, val in raw["symbols"]:
            self.back.setdefault(val, _norm(key))
        for key, val in raw["abbrev"]:
            self.back.setdefault(val, _norm(key))

    # ---------- compile ----------
    def compile(self, text: str) -> str:
        out_lines: list[str] = []
        for line in text.splitlines():
            if not line.strip():
                continue
            prefix = TREE_PREFIX.match(line)
            lead = prefix.group(0).replace("*", "·") if prefix else ""
            body = line[prefix.end():] if prefix else line
            body = self._strip_filler(body)
            body = self._compress_line(body)
            body = self._tidy(body)
            if self.level >= 2:
                body = body.replace("。", ".").replace("：", ":")
            if self.level >= 3:
                body = self._tidy(self._drop_particles(body))
            if not body:
                continue
            out_lines.append((lead.rstrip() + " " if lead.strip() else "") + body)
        return "\n".join(out_lines)

    def _strip_filler(self, line: str) -> str:
        for f in MID_FILLER:
            line = line.replace(f, "")
        low = line.lower()
        changed = True
        while changed:
            changed = False
            for f in self.filler:
                if low.startswith(f):
                    line, low = line[len(f):], low[len(f):]
                    line, low = line.lstrip(" ，,：:　"), low.lstrip(" ，,：:　")
                    changed = True
                    break
        return line

    def _compress_line(self, line: str) -> str:
        # 1. protect facts
        slots: dict[str, str] = {}
        def protect(m: re.Match) -> str:
            key = f"\x00{len(slots)}\x00"
            slots[key] = m.group(0)
            return key

        guard = re.compile("|".join(f"(?:{p.pattern})" for _, p in ENTITY_PATTERNS))
        line = guard.sub(protect, line)

        # 2. lexicon: longest phrase first, case-insensitive, spaced so latin
        #    replacements never fuse into unreadable blobs ("reqparam")
        for table in (self.intent, self.abbrev, self.symbols):
            for src, dst in table:
                if src in line.lower():
                    line = re.sub(re.escape(src), lambda _m, d=dst: f" {d} ", line, flags=re.I)
        # 3. restore facts
        for key, val in slots.items():
            line = line.replace(key, val)
        # 4. clause minimisation (level 2+; level 1 keeps original punctuation)
        if self.level >= 2:
            line = re.sub(r"[，,]\s*", " ; ", line)
        line = re.sub(r"\s*(?:并且|而且)\s*", " ∧ ", line)
        return line

    def _drop_particles(self, line: str) -> str:
        """Level 3 only: strip low-signal CJK particles between CJK characters."""
        line = re.sub(r"(?<=[\u4e00-\u9fff\w])\s*的\s*(?=[\u4e00-\u9fff])", "", line)
        line = re.sub(r"(?<=[\u4e00-\u9fff\w])\s*[了吗呢吧啊](?=[，,。;；.\s]|$)", "", line)
        return line

    def _tidy(self, line: str) -> str:
        line = re.sub(r"\s{2,}", " ", line).strip()
        line = re.sub(r"(?:\s*;\s*)+", " ; ", line)
        line = re.sub(r"\s+([)）,.;:])", r"\1", line)
        return line.strip(" ;，,")

    # ---------- decode ----------
    def decode(self, text: str) -> str:
        """Approximate back-translation for human review.

        Latin abbreviations are only reversed at token boundaries so that
        'Python' never becomes 'Pyth基于代码'; single-character operators are
        left alone because '!' or '=' expand ambiguously.
        """
        skip = {"!", "?", "=", ">", "<", "∅"}
        out = []
        for line in text.splitlines():
            # facts stay out of the reverse pass, exactly like compile
            slots: dict[str, str] = {}

            def protect(m: re.Match) -> str:
                key = f"\x01{len(slots)}\x01"
                slots[key] = m.group(0)
                return key

            guard = re.compile("|".join(f"(?:{p.pattern})" for p in DECODE_GUARDS))
            s = guard.sub(protect, line)
            for symbol, src in sorted(self.back.items(), key=lambda p: -len(p[0])):
                if symbol in skip or len(symbol) < 2 or symbol in self.decode_skip:
                    continue
                if re.fullmatch(r"[\x20-\x7e]+", symbol) and re.search(r"[A-Za-z0-9]", symbol):
                    s = re.sub(rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])",
                               f" {src} ", s, flags=re.I)
                else:
                    s = s.replace(symbol, f" {src} ")
            for key, val in slots.items():
                s = s.replace(key, val)
            s = re.sub(r"\s{2,}", " ", s).strip()
            out.append(s)
        return "\n".join(out)


FACT_KINDS = {"url", "ipv4", "path", "quoted", "number", "ident", "domain", "param"}


def entities(text: str, facts_only: bool = False) -> list[str]:
    """Entities in a text. facts_only drops acronyms, which compression adds by
    design and which would otherwise pollute the fidelity ratio."""
    found: list[str] = []
    for kind, pat in ENTITY_PATTERNS:
        if facts_only and kind not in FACT_KINDS:
            continue
        found.extend(pat.findall(text))
    return found


def est_tokens(text: str) -> int:
    """Rough token estimate. Punctuation and separators are free — counting them
    would penalise clause splitting and make the density metric lie."""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9_]+", text))
    return cjk + math.ceil(latin * 1.3)


def fidelity_check(src: str, dst: str) -> dict:
    src_ents, dst_ents = entities(src, True), entities(dst, True)
    missing = [e for e in src_ents if e not in dst_ents]
    added = [e for e in dst_ents if e not in src_ents]
    src_tok, dst_tok = est_tokens(src), est_tokens(dst)
    return {
        "entities_src": len(src_ents),
        "entities_dst": len(dst_ents),
        "entity_retention": round(1 - len(missing) / max(1, len(src_ents)), 3),
        "missing": missing[:20],
        "added": added[:20],
        "tokens_src": src_tok,
        "tokens_dst": dst_tok,
        "compression": round(dst_tok / max(1, src_tok), 3),
        "chars_src": len(src),
        "chars_dst": len(dst),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BabelTele compiler")
    ap.add_argument("mode", choices=["compile", "decode", "check", "list"])
    ap.add_argument("--in", dest="infile")
    ap.add_argument("--out", dest="outfile")
    ap.add_argument("--src")
    ap.add_argument("--dst")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--level", type=int, default=2, choices=[1, 2, 3],
                    help="1=lexicon only, 2=+clause split (default), 3=+particle drop")
    args = ap.parse_args(argv)

    babel = Babel(level=args.level)

    if args.mode == "list":
        print(json.dumps({"intent": len(babel.intent), "symbols": len(babel.symbols),
                          "abbrev": len(babel.abbrev), "filler": len(babel.filler)},
                         ensure_ascii=False, indent=2))
        return 0

    if args.mode in ("compile", "decode"):
        text = Path(args.infile).read_text("utf-8") if args.infile else sys.stdin.read()
        result = babel.compile(text) if args.mode == "compile" else babel.decode(text)
        if args.outfile:
            Path(args.outfile).write_text(result + "\n", "utf-8")
            print(f"[ok] {args.outfile}", file=sys.stderr)
        else:
            print(result)
        return 0

    if not (args.src and args.dst):
        ap.error("check needs --src and --dst")
    src, dst = Path(args.src).read_text("utf-8"), Path(args.dst).read_text("utf-8")
    report = fidelity_check(src, dst)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        verdict = "PASS" if not report["missing"] and report["entity_retention"] == 1.0 else "FAIL"
        print(f"[{verdict}] entity_retention={report['entity_retention']} "
              f"compression={report['compression']} tokens {report['tokens_src']}->{report['tokens_dst']}")
        for e in report["missing"]:
            print(f"  missing: {e!r}")
    return 0 if report["entity_retention"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
