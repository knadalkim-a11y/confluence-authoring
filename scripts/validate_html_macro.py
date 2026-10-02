#!/usr/bin/env python3
"""Static safety/compatibility checks for rendered Confluence HTML macro fragments."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TOKEN_RE = re.compile(r"{{([A-Z0-9_]+)}}")
BANNED_TAGS = ("html", "head", "body", "script", "iframe")
EXTERNAL_PATTERNS = (
    re.compile(r"https?://", re.I),
    re.compile(r"(?:src|href)\s*=\s*['\"]//", re.I),
    re.compile(r"url\(\s*['\"]?https?://", re.I),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fragment", type=Path)
    parser.add_argument("--allow-template-tokens", action="store_true")
    args = parser.parse_args()

    text = args.fragment.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    for tag in BANNED_TAGS:
        if re.search(rf"<\s*{tag}\b", text, re.I):
            errors.append(f"banned tag present: <{tag}>")

    for pattern in EXTERNAL_PATTERNS:
        if pattern.search(text):
            errors.append("external network dependency detected")
            break

    unresolved = sorted(set(TOKEN_RE.findall(text)))
    if unresolved and not args.allow_template_tokens:
        errors.append("unresolved template tokens: " + ", ".join(unresolved))

    if "<style" not in text.lower():
        warnings.append("no <style> block found")
    if "prefers-reduced-motion" not in text:
        errors.append("missing prefers-reduced-motion fallback")
    if "@media print" not in text:
        errors.append("missing print/static fallback")
    if "animation" not in text.lower():
        warnings.append("no animation rule detected; this may be a static fragment")

    print(f"file: {args.fragment}")
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"FAIL: {error}")

    if errors:
        print(f"result: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1

    print(f"result: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
