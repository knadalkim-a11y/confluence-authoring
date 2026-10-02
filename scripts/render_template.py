#!/usr/bin/env python3
"""Render a Confluence authoring template with a unique prefix and token values."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TOKEN_RE = re.compile(r"{{([A-Z0-9_]+)}}")
PREFIX_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]{2,40}$")


def parse_sets(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise SystemExit(f"Invalid --set value: {item!r}; expected KEY=value")
        key, value = item.split("=", 1)
        key = key.strip().upper()
        if not re.fullmatch(r"[A-Z0-9_]+", key):
            raise SystemExit(f"Invalid token name: {key!r}")
        result[key] = value
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=value")
    parser.add_argument("--allow-unresolved", action="store_true")
    args = parser.parse_args()

    if not PREFIX_RE.fullmatch(args.prefix):
        raise SystemExit("Prefix must start with a letter and contain only letters, numbers, or hyphens (3-41 chars).")

    source = args.template.read_text(encoding="utf-8")
    values = parse_sets(args.sets)
    values["PREFIX"] = args.prefix

    rendered = source
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)

    unresolved = sorted(set(TOKEN_RE.findall(rendered)))
    if unresolved and not args.allow_unresolved:
        raise SystemExit("Unresolved template tokens: " + ", ".join(unresolved))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"rendered: {args.output}")
    if unresolved:
        print("warning: unresolved tokens allowed: " + ", ".join(unresolved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
