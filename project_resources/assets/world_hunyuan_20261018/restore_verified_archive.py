#!/usr/bin/env python3
"""Restore one SHA-256/CRC checked archive from a pinned GitHub commit.
Python 3 standard library only. Existing changed files are never overwritten.
"""
import argparse,hashlib,json,shutil,stat,time,urllib.request,zipfile
from pathlib import Path,PurePosixPath

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def download(url,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.download')
 for attempt in range(4):
  try:
   with urllib.request.urlopen(url,timeout=120) as r,tmp.open('wb') as out:shutil.copyfileobj(r,out,1024*1024)
   tmp.replace(path);return
  except Exception:
   if attempt==3:raise
   time.sleep(2**attempt)
def restore(base,manifest_name,cache,out):
 cache.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
 mf=cache/manifest_name;download(base+'/'+manifest_name,mf);m=json.loads(mf.read_text())
 assembled=cache/m['archive']
 with assembled.open('wb') as dst:
  for p in m['parts']:
   f=cache/'archives'/p['name']
   if not f.exists() or f.stat().st_size!=p['size'] or digest(f)!=p['sha256']:download(base+'/archives/'+p['name'],f)
   if f.stat().st_size!=p['size'] or digest(f)!=p['sha256']:raise RuntimeError('Part integrity: '+p['name'])
   with f.open('rb') as src:shutil.copyfileobj(src,dst,1024*1024)
 if assembled.stat().st_size!=m['archive_size'] or digest(assembled)!=m['archive_sha256']:raise RuntimeError('Archive integrity mismatch')
 expected={r['path']:r for r in m['files']}
 with zipfile.ZipFile(assembled) as z:
  bad=z.testzip()
  if bad:raise RuntimeError('ZIP CRC failure: '+bad)
  names=[i.filename for i in z.infolist() if not i.is_dir()]
  if len(names)!=len(set(names)) or set(names)!=set(expected):raise RuntimeError('ZIP member inventory mismatch')
  for info in z.infolist():
   n=PurePosixPath(info.filename)
   if n.is_absolute() or '..' in n.parts or '\\' in info.filename or stat.S_ISLNK(info.external_attr>>16):raise RuntimeError('Unsafe ZIP member: '+info.filename)
   dest=(out/info.filename).resolve()
   if out.resolve() not in dest.parents:raise RuntimeError('Path escape')
   if info.is_dir():continue
   if dest.exists():
    if digest(dest)!=expected[info.filename]['sha256']:raise RuntimeError('Changed existing file: '+str(dest))
   else:z.extract(info,out)
 for name,r in expected.items():
  f=out/name
  if f.stat().st_size!=r['size'] or digest(f)!=r['sha256']:raise RuntimeError('Restored file mismatch: '+name)
 print(m['archive'],len(expected),'internal files verified')
 return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ref',required=True,help='Full commit SHA, never floating main');p.add_argument('--prefix',required=True);p.add_argument('--manifest',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cache',type=Path,default=Path('download_cache'));a=p.parse_args()
 if len(a.ref)!=40 or any(c not in '0123456789abcdef' for c in a.ref.lower()):p.error('--ref must be a full hexadecimal commit SHA')
 restore('https://raw.githubusercontent.com/coolzhulike/gamedemo/'+a.ref+'/'+a.prefix,a.manifest,a.cache,a.output)
