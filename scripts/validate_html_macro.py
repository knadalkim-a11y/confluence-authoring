#!/usr/bin/env python3
"""Conservative offline-macro lint, not an HTML sanitizer or a browser substitute."""
from __future__ import annotations
import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

LIVE_MARK='/*ca-live-runtime v1*/'
# Live fragments may carry exactly one inline runtime script per live root. These APIs
# would add network, storage, dynamic code or cross-page effects and are never allowed.
LIVE_FORBIDDEN=re.compile(r'\b(?:fetch|XMLHttpRequest|WebSocket|EventSource|importScripts|eval|Function|localStorage|sessionStorage|indexedDB|cookie|postMessage|sendBeacon|open)\s*\(|\bimport\s*\(|document\.write|\.src\s*=|innerHTML\s*=\s*[^;]*location|window\.location|top\.|parent\.')
BAD_TAGS={'html','head','body','script','iframe','object','embed','link','base','meta','form','foreignobject','animate','animatetransform','set','image','audio','video','source'}
TOKEN=re.compile(r'{{[A-Z][A-Z0-9_]*}}')


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[]
        self.refs=[]
        self.prefixes=[]
        self.styles=[]
        self.errors=[]
        self.in_style=False
        self.inline_styles=[]
        self.in_script=False
        self.scripts=[]
        self.live_roots=0
        self.static_svgs=0

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('data-ca-runtime')=='live':
            self.live_roots+=1
        if tag=='svg' and 'data-ca-static' in attrs:
            self.static_svgs+=1
        if tag=='script':
            self.in_script=True
            self.scripts.append('')
            if attrs:
                self.errors.append('Live script must not have attributes')
            return
        if tag in BAD_TAGS:
            self.errors.append(f'Forbidden tag: {tag}')
        self.in_style=tag=='style' or self.in_style
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'data-ca-prefix' in attrs:
            self.prefixes.append(attrs['data-ca-prefix'])
        if tag=='label' and 'for' in attrs:
            self.refs.append(attrs['for'])
        for key in ['aria-labelledby','aria-describedby']:
            if attrs.get(key):
                self.refs.extend(attrs[key].split())
        for key,value in attrs.items():
            value=value or ''
            if key.lower().startswith('on') or key in {'srcdoc','src','srcset','action','formaction'}:
                self.errors.append(f'Unsafe/resource attribute: {key}')
            if key in {'href','xlink:href'}:
                if value.startswith('#'):
                    self.refs.append(value[1:])
                elif tag=='a' and re.match(r'https?://[^\s]+$',value):
                    pass  # navigation is not an external runtime dependency
                else:
                    self.errors.append(f'Nonlocal reference: {key}')
            if key=='style':
                self.inline_styles.append(value)

    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)

    def handle_endtag(self,tag):
        if tag=='style':
            self.in_style=False
        if tag=='script':
            self.in_script=False

    def handle_data(self,data):
        if self.in_script:
            self.scripts[-1]+=data
            return
        if self.in_style:
            self.styles.append(data)


def blocks(css):
    """Yield balanced CSS blocks while respecting strings; fail on malformed CSS."""
    position=0
    while position<len(css):
        opening=css.find('{',position)
        if opening<0:
            if css[position:].strip():
                raise ValueError('CSS outside a block')
            return
        header=css[position:opening].strip()
        depth=1
        quote=None
        i=opening+1
        while i<len(css) and depth:
            char=css[i]
            if quote:
                if char==quote:
                    quote=None
            elif char in {'"',"'"}:
                quote=char
            elif char=='{':
                depth+=1
            elif char=='}':
                depth-=1
            i+=1
        if depth:
            raise ValueError('Unbalanced CSS')
        yield header,css[opening+1:i-1]
        position=i


def validate(fragment: str) -> list[str]:
    p=Inspector()
    p.feed(fragment)
    errors=list(p.errors)
    if p.scripts:
        if p.live_roots!=len(p.scripts):
            errors.append('Forbidden tag: script')
        for body in p.scripts:
            if not body.startswith(LIVE_MARK):
                errors.append('Script is not the bundled live runtime')
            if LIVE_FORBIDDEN.search(body):
                errors.append('Live script uses a forbidden API')
        if p.static_svgs<p.live_roots:
            errors.append('Live fragment lacks a static fallback SVG')
    elif p.live_roots:
        errors.append('Live root without runtime script')
    if TOKEN.search(fragment):
        errors.append('Unresolved template token')
    if not p.prefixes or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{2,40}',x or '') for x in p.prefixes):
        errors.append('Missing/invalid data-ca-prefix')
    if len(p.prefixes)!=len(set(p.prefixes)):
        errors.append('Duplicate prefix')
    if len(p.ids)!=len(set(p.ids)):
        errors.append('Duplicate ID')
    for ref in p.refs:
        if ref not in p.ids:
            errors.append(f'Unresolved ID reference: {ref}')
    for value in p.ids:
        if not any(value.startswith(prefix+'-') for prefix in p.prefixes if prefix):
            errors.append(f'Unscoped ID: {value}')
    css=re.sub(r'/\*.*?\*/','','\n'.join(p.styles),flags=re.S)
    all_css=css+'\n'+'\n'.join(p.inline_styles)
    if re.search(r'@import|expression\s*\(|javascript\s*:|-moz-binding|behavior\s*:',all_css,re.I) or '\\' in all_css:
        errors.append('Unsupported/unsafe CSS construct')
    for match in re.finditer(r'url\(\s*[\'\"]?([^\)\'\"]+)',all_css,re.I):
        reference=match[1].strip()
        if not reference.startswith('#') or reference[1:] not in p.ids:
            errors.append('External/unresolved CSS URL')
    keyframes=[]
    def check(source,keyframe=False):
        for head,body in blocks(source):
            if head.startswith('@keyframes '):
                name=head.split()[-1]
                keyframes.append(name)
                if not any(name.startswith(prefix+'-') for prefix in p.prefixes if prefix):
                    errors.append(f'Unscoped keyframe: {name}')
                check(body,True)
            elif head.startswith(('@media ','@container ','@supports ')):
                check(body)
            elif head.startswith('@'):
                errors.append(f'Unsupported at-rule: {head}')
            elif keyframe:
                if any(not re.fullmatch(r'(from|to|\d+(?:\.\d+)?%)',x.strip()) for x in head.split(',')):
                    errors.append('Invalid keyframe selector')
            else:
                for selector in head.split(','):
                    if not any(re.match(r'\.'+re.escape(prefix)+r'(?=$|[\s.:#\[])',selector.strip()) for prefix in p.prefixes if prefix):
                        errors.append(f'Unscoped selector: {selector.strip()}')
    try:
        check(css)
    except ValueError as e:
        errors.append(str(e))
    if len(keyframes)!=len(set(keyframes)):
        errors.append('Duplicate keyframes')
    for name in re.findall(r'--[ab]\s*:\s*([^;}]+)',css):
        if name.strip() not in keyframes:
            errors.append(f'Undefined animation: {name}')
    if 'prefers-reduced-motion' not in css:
        errors.append('Missing reduced-motion fallback')
    if not re.search(r'@media\s+print',css):
        errors.append('Missing print fallback')
    return sorted(set(errors))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('fragment',type=Path)
    args=p.parse_args()
    try:
        errors=validate(args.fragment.read_text(encoding='utf-8'))
    except (OSError,ValueError) as e:
        errors=[str(e)]
    for error in errors:
        print('FAIL:',error)
    print('FAIL' if errors else 'PASS',args.fragment)
    return bool(errors)

if __name__=='__main__':
    raise SystemExit(main())
