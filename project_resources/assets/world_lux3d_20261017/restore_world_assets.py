#!/usr/bin/env python3
"""Download, verify and restore the archived world assets using Python 3 only."""
import argparse,hashlib,json,shutil,tempfile,urllib.request,zipfile
from pathlib import Path
REPO='coolzhulike/gamedemo'; BRANCH='assets/world-lux3d-20261017'; PREFIX='project_resources/assets/world_lux3d_20261017'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def get(url,p):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.download')
 with urllib.request.urlopen(url,timeout=120) as r,tmp.open('wb') as f:shutil.copyfileobj(r,f,1024*1024)
 tmp.replace(p)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=Path('restored_world_assets'));ap.add_argument('--ref',default=BRANCH);a=ap.parse_args();here=Path(__file__).resolve().parent;base=f'https://raw.githubusercontent.com/{REPO}/{a.ref}/{PREFIX}'
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True);index=here/'bundle_index.json'
 if not index.exists():get(base+'/bundle_index.json',index)
 for name in json.loads(index.read_text())['manifests']:
  mf=here/name
  if not mf.exists():get(base+'/'+name,mf)
  m=json.loads(mf.read_text());assembled=out/('.'+m['archive']+'.restoring')
  try:
   with assembled.open('wb') as dst:
    for p in m['parts']:
     local=here/'archives'/p['name']
     if not local.exists() or local.stat().st_size!=p['size'] or digest(local)!=p['sha256']:get(base+'/archives/'+p['name'],local)
     if local.stat().st_size!=p['size'] or digest(local)!=p['sha256']:raise RuntimeError('Part hash mismatch: '+p['name'])
     with local.open('rb') as src:shutil.copyfileobj(src,dst,1024*1024)
   if digest(assembled)!=m['archive_sha256']:raise RuntimeError('Archive hash mismatch')
   with zipfile.ZipFile(assembled) as z:
    bad=z.testzip()
    if bad:raise RuntimeError('ZIP CRC mismatch: '+bad)
    for member in z.infolist():
     target=(out/member.filename).resolve()
     if out not in target.parents:raise RuntimeError('Unsafe ZIP path')
     if target.exists():
      rec=next(x for x in m['files'] if x['path']==member.filename)
      if digest(target)!=rec['sha256']:raise RuntimeError('Refusing to overwrite existing changed file: '+str(target))
     else:z.extract(member,out)
   for rec in m['files']:
    f=out/rec['path']
    if f.stat().st_size!=rec['size'] or digest(f)!=rec['sha256']:raise RuntimeError('Restored file mismatch: '+rec['path'])
   print(m['archive'],'verified:',len(m['files']),'files',flush=True)
  finally:
   if assembled.exists():assembled.unlink()
 print('Restored:',out)
if __name__=='__main__':main()
