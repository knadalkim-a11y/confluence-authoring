#!/usr/bin/env python3
"""Build standalone gallery and 13 copy-ready examples, using the production renderer."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from motion import ROOT, FIELDS, render, document
from validate_html_macro import validate


def build(output: Path) -> dict:
    catalog=json.loads((ROOT/'references/motion-catalog.yaml').read_text(encoding='utf-8'))
    examples=json.loads((ROOT/'examples/motion-inputs.json').read_text(encoding='utf-8'))
    output.mkdir(parents=True,exist_ok=True)
    payload=[]
    sizes={}
    patterns=[x for x in catalog['patterns'] if x['status']=='implemented']
    if {x['id'] for x in patterns}!=set(FIELDS) or set(examples)!=set(FIELDS):
        raise ValueError('Catalog, renderer and examples disagree')
    for i,item in enumerate(patterns):
        key=item['id']
        fragment=render(key,examples[key],f'ca-demo-{i:02d}')
        errors=validate(fragment)
        if errors:
            raise ValueError(f'{key}: {errors}')
        (output/f'{key}.macro.html').write_text(fragment,encoding='utf-8')
        (output/f'{key}.preview.html').write_text(document(fragment),encoding='utf-8')
        (output/f'{key}.input.json').write_text(json.dumps(examples[key],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        payload.append({key:item[key] for key in ['id','title','category','best_for','avoid_when']}|{'html':fragment})
        sizes[key]=len(fragment.encode('utf-8'))
    source=(ROOT/'gallery/index.html').read_text(encoding='utf-8')
    # Escape '<' to prevent script termination even when sample text contains HTML.
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    gallery=source.replace('<!-- BUILD_DATA -->','<script>window.CA_GALLERY='+data+';</script>')
    (output/'gallery.html').write_text(gallery,encoding='utf-8')
    manifest={'version':'0.2.0','patterns':len(payload),'macro_bytes':sizes,'gallery_bytes':len(gallery.encode('utf-8')),'javascript_in_macros':False,'confluence_verified':False}
    (output/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'dist')
    print(json.dumps(build(p.parse_args().output),ensure_ascii=False,indent=2))
