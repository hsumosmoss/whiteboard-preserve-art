#!/usr/bin/env python3
"""Portable manifest checker. Python 3.9+. Does not render or visually verify media."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROUTE = 'preserve'

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def validate(root):
    errors = []
    def fail(message): errors.append(message)
    def number(v): return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    def file(value, label):
        if not isinstance(value, str) or not value:
            fail(label + ': missing path'); return None
        p = (root / value).resolve()
        if not p.is_relative_to(root.resolve()):
            fail(label + ': path outside project'); return None
        if not p.is_file() or not p.stat().st_size:
            fail(label + ': missing or empty file'); return None
        return p
    def objects(v, label):
        if not isinstance(v, list) or not all(isinstance(x, dict) for x in v):
            fail(label + ': expected list of objects'); return []
        return v
    try:
        m = json.loads((root/'project.json').read_text(encoding='utf-8'))
        if not isinstance(m, dict): raise ValueError('project must be an object')
    except (OSError, ValueError) as e:
        return ['Cannot read project: ' + str(e)]
    if m.get('route') != ROUTE: fail('Route does not match this skill')
    if m.get('stage') not in {'draft','planned','production','complete'}: fail('Unknown stage')
    if m.get('stage') == 'draft': return errors
    canvas = m.get('canvas', {})
    if not isinstance(canvas, dict): canvas = {}
    for key in ['width','height','fps']:
        if not number(canvas.get(key)) or canvas[key] <= 0: fail('Invalid canvas '+key)
    total = m.get('duration')
    if not number(total) or total <= 0: fail('Invalid total duration'); total = None
    assets = objects(m.get('assets', []), 'assets'); amap = {}
    for a in assets:
        key = a.get('id')
        if not isinstance(key, str) or not key: fail('Asset needs ID'); continue
        if key in amap: fail('Duplicate asset ID: '+key)
        amap[key] = a
        if m.get('stage') not in {'production','complete'}: continue
        if ROUTE == 'preserve':
            p = file(a.get('source'), key+' source')
            if p and digest(p) != a.get('source_sha256'): fail(key+': source hash mismatch')
            size, crop = a.get('source_size'), a.get('crop')
            if not (isinstance(size, list) and len(size)==2 and all(number(v) and v>0 for v in size)):
                fail(key+': invalid source_size'); size = None
            if not (isinstance(crop, list) and len(crop)==4 and all(number(v) for v in crop)):
                fail(key+': invalid crop')
            elif size and not (0<=crop[0]<crop[2]<=size[0] and 0<=crop[1]<crop[3]<=size[1]): fail(key+': crop outside source')
            path = file(a.get('reveal_file'), key+' reveal')
            path_kind = 'paths'
        else:
            path = file(a.get('path_file'), key+' strokes')
            path_kind = 'strokes'
            if a.get('preview'): file(a['preview'],key+' preview')
        if path:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(data, dict): raise ValueError('geometry must be an object')
                for dimension in ['width','height']:
                    if not number(data.get(dimension)) or data[dimension]<=0: raise ValueError('invalid geometry dimensions')
                paths = data.get(path_kind)
                if not isinstance(paths,list) or not paths: raise ValueError('no '+path_kind)
                for line in paths:
                    pts = line['points']
                    if not isinstance(pts,list) or len(pts)<2 or not all(isinstance(p,list) and len(p)==2 and all(number(v) for v in p) for p in pts): raise ValueError('invalid points')
                    if sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))<=0: raise ValueError('zero-length path')
                    width = line.get('brush_width' if ROUTE=='preserve' else 'width')
                    if not number(width) or width<=0: raise ValueError('invalid width')
            except (OSError,ValueError,KeyError,TypeError) as e: fail(key+': invalid '+path_kind+': '+str(e))
    scenes = objects(m.get('scenes',[]),'scenes'); intervals=[];seen=set()
    if not scenes: fail('No scenes')
    for s in scenes:
        sid=s.get('id'); start,end=s.get('start'),s.get('end')
        if not isinstance(sid,str) or not sid: fail('Scene needs ID');sid='?'
        if sid in seen: fail('Duplicate scene ID: '+sid)
        seen.add(sid)
        valid=number(start) and number(end) and 0<=start<end
        if not valid: fail(sid+': invalid timing')
        else:
            intervals.append((start,end))
            if total is not None and end>total+1e-6: fail(sid+': exceeds total duration')
        draws=[]
        for item in objects(s.get('items',[]),sid+' items'):
            key=item.get('asset_id')
            if not isinstance(key,str) or key not in amap: fail(sid+': unknown asset')
            t,d=item.get('start'),item.get('duration')
            if not (number(t) and number(d) and t>=0 and d>0): fail(sid+': invalid drawing timing')
            else:
                draws.append((t,t+d))
                if valid and t+d>end-start+1e-6: fail(sid+': drawing exceeds scene')
            for k in ['x','y','width']:
                if not number(item.get(k)) or (k=='width' and item[k]<=0): fail(sid+': invalid item '+k)
        if not m.get('multiple_pens',False):
            for p,q in zip(sorted(draws),sorted(draws)[1:]):
                if q[0]<p[1]-1e-6: fail(sid+': overlapping single-pen draws')
    for p,q in zip(sorted(intervals),sorted(intervals)[1:]):
        if q[0]<p[1]-1e-6: fail('Overlapping scenes')
    last=0
    for c in objects(m.get('cues',[]),'cues'):
        a,b=c.get('start'),c.get('end')
        if not (number(a) and number(b) and 0<=a<b): fail('Invalid cue timing');continue
        if a<last-1e-6: fail('Overlapping or unsorted cues')
        if total is not None and b>total+1e-6: fail('Cue exceeds duration')
        if not isinstance(c.get('text'),str) or not c['text'].strip(): fail('Empty cue')
        last=b
    chapters=objects(m.get('chapters',[]),'chapters');cids={}
    for c in chapters:
        cid=c.get('id')
        if not isinstance(cid,str) or not cid:fail('Chapter needs ID');continue
        if cid in cids:fail('Duplicate chapter ID')
        cids[cid]=c
    chapter_pages=set()
    for p in objects(m.get('ebook_pages',[]),'ebook_pages'):
        cid=p.get('chapter_id');typ=p.get('type')
        if typ not in {'cover','chapter','content'}:fail('Unknown ebook page type')
        if cid is not None and (not isinstance(cid,str) or cid not in cids):fail('Unknown ebook chapter')
        if typ=='chapter':
            if not isinstance(cid,str) or cid not in cids:fail('Chapter page needs valid chapter_id')
            else:chapter_pages.add(cid)
        if typ=='content' and isinstance(cid,str) and cid not in chapter_pages:fail('Missing chapter page before content')
    outputs=objects(m.get('outputs',[]),'outputs');kinds=set()
    for o in outputs:
        if isinstance(o.get('kind'),str):kinds.add(o['kind'])
        file(o.get('path'),'output')
    if m.get('stage')=='complete':
        selected=m.get('deliverables',[])
        if not isinstance(selected,list) or not all(isinstance(x,str) for x in selected):fail('Invalid deliverables');selected=[]
        for key in selected:
            if key not in kinds:fail('Missing selected output: '+key)
        for cid,c in cids.items():
            if 'ebook' in c.get('targets',[]) and cid not in chapter_pages:fail('Missing chapter divider: '+cid)
        if 'video' in selected and m.get('timing_basis')!='measured' and not (m.get('audio_status')=='unavailable' and m.get('limitations')):fail('No measured timing or declared audio limitation')
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['init','check','hash']:
        sub.add_parser(name).add_argument('path',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='hash':print(digest(args.path));return 0
        if args.command=='init':
            args.path.mkdir(parents=True,exist_ok=True);p=args.path/'project.json'
            with p.open('x',encoding='utf-8') as f:json.dump({'route':ROUTE,'stage':'draft','duration':None,'canvas':{},'deliverables':[],'assets':[],'scenes':[],'cues':[],'chapters':[],'ebook_pages':[],'outputs':[]},f,ensure_ascii=False,indent=2)
            print(p);return 0
        errors=validate(args.path)
        if errors:
            for e in errors:print('ERROR:',e)
            return 1
        print('Manifest check passed. Media and visual verification remain separate.');return 0
    except (OSError,ValueError) as e:print('ERROR:',e);return 1

if __name__=='__main__':raise SystemExit(main())
