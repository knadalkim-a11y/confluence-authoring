#!/usr/bin/env python3
"""Build all reference cases, or a single explicitly synthetic case. No publishing."""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
from reference_scene import ROOT,document,esc
from monitoring_cases import build_case
from validate_html_macro import validate

def catalogue():
    return json.loads((ROOT/'examples/monitoring-cases.json').read_text(encoding='utf-8'))

def build_all(output:Path,speed=1.25,baseline:Path|None=None):
    data=catalogue();items=[];output.mkdir(parents=True,exist_ok=True)
    for index,meta in enumerate(data['cases']):
        prefix=f'ca-monitor-{index:02d}';fragment,model=build_case(meta,prefix,speed=speed)
        errors=validate(fragment)
        if errors:raise ValueError(meta['id']+': '+';'.join(errors))
        folder=output/meta['id'];folder.mkdir(parents=True,exist_ok=True)
        (folder/'macro.html').write_text(fragment,encoding='utf8')
        (folder/'macro.txt').write_text(fragment,encoding='utf8')
        (folder/'preview.html').write_text(document(fragment,meta['title']),encoding='utf8')
        (folder/'input.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        (folder/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        item=copy.deepcopy(meta);item['reference_duration']=18;item['default_speed']=speed;item['macro']=fragment;
        # Before/after toggle for reworked cases: the layout revisions and every live-tier case.
        if baseline and (meta.get('runtime')=='live' or meta['id'] in ('cluster-cascade','event-loop')):
            old=baseline/meta['id']/'macro.html'
            if old.is_file():item['baseline_macro']=old.read_text(encoding='utf8')
        item['bytes']=len(fragment.encode());item['sha256']=hashlib.sha256(fragment.encode()).hexdigest();items.append(item)
    source=(ROOT/'gallery/monitoring-suite.html').read_text(encoding='utf8')
    # Prevent data strings from closing the JSON script element.
    bundle=json.dumps(items,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    page=source.replace('%%CASES_JSON%%',bundle)
    (output/'gallery.html').write_text(page,encoding='utf8')
    manifest={k:v for k,v in data.items() if k!='cases'}
    manifest.update(in_article_count=sum(x['in_article'] for x in items),bonus_count=sum(not x['in_article'] for x in items),cases=[{k:v for k,v in x.items() if k not in ('macro','baseline_macro')} for x in items])
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'dist/monitoring-suite');p.add_argument('--case');p.add_argument('--input',type=Path);p.add_argument('--prefix');p.add_argument('--speed',type=float,choices=[1,1.25,1.5],default=1.25);p.add_argument('--baseline',type=Path,help='Optional previous build output; layout-revised and live cases get an "이전 버전 보기" toggle')
    args=p.parse_args()
    try:
        if args.case:
            meta=next((x for x in catalogue()['cases'] if x['id']==args.case),None)
            if meta is None:raise ValueError('Unknown case')
            if args.input:meta=json.loads(args.input.read_text(encoding='utf8'))
            if meta['id']!=args.case:raise ValueError('Case/input ID mismatch')
            fragment,model=build_case(meta,args.prefix,speed=args.speed);errors=validate(fragment)
            if errors:raise ValueError('; '.join(errors))
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'macro.html').write_text(fragment,encoding='utf8');(args.output/'preview.html').write_text(document(fragment,meta['title']),encoding='utf8');(args.output/'model.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf8')
            print('PASS',args.case,args.output)
        else:
            if args.input or args.prefix:raise ValueError('--input/--prefix require --case')
            result=build_all(args.output,speed=args.speed,baseline=args.baseline);print(f'PASS: {result["in_article_count"]} article cases + {result["bonus_count"]} bonus; {args.output/"gallery.html"}')
        return 0
    except (ValueError,KeyError,TypeError,OSError,OverflowError) as e:
        print('FAIL:',str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
