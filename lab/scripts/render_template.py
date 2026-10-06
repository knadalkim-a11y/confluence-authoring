#!/usr/bin/env python3
"""Legacy escaped text-template rendering; use render_motion.py for v0.2 scenes."""
from __future__ import annotations
import argparse
import html
import re
import sys
from pathlib import Path
from motion import ROOT, PREFIX, TOKEN


def parse_sets(items):
    values={}
    for item in items:
        if '=' not in item:
            raise ValueError('--set requires KEY=value')
        key,value=item.split('=',1)
        key=key.strip().upper()
        if not re.fullmatch('[A-Z][A-Z0-9_]*',key) or key in values or key=='PREFIX':
            raise ValueError('Invalid, repeated, or reserved --set key')
        values[key]=html.escape(value,quote=True)
    return values


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('template',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--prefix',required=True)
    p.add_argument('--set',dest='sets',action='append',default=[])
    p.add_argument('--allow-unresolved',action='store_true')
    args=p.parse_args()
    try:
        if not PREFIX.fullmatch(args.prefix):
            raise ValueError('Invalid prefix')
        if args.template.resolve().parent==ROOT/'visuals/motion':
            raise ValueError('v0.2 scene source: use render_motion.py PATTERN OUTPUT --input INPUT.json (or --example). Text-only overrides cannot safely update chart geometry.')
        source=args.template.read_text(encoding='utf-8')
        values=parse_sets(args.sets)
        values['PREFIX']=args.prefix
        missing=set(TOKEN.findall(source))-values.keys()
        if missing and not args.allow_unresolved:
            raise ValueError('Unresolved tokens: '+','.join(sorted(missing)))
        rendered=TOKEN.sub(lambda m:values.get(m[1],m[0]),source)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered,encoding='utf-8')
        print('DRAFT (unresolved tokens)' if missing else 'Rendered',args.output)
        return 0
    except (OSError,ValueError) as e:
        print('FAIL:',e,file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
