"""Download all verified parts from this branch, reconstruct ZIP and verify assets.
Python 3 standard library only. Run in an empty directory with sufficient space.
"""
from pathlib import Path
import hashlib,json,urllib.request,zipfile,shutil
BASE='https://raw.githubusercontent.com/coolzhulike/gamedemo/assets/highpoly-characters-20261017/project_resources/assets/characters_20261017/archive/'
HERE=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()

def obtain(name,expected=None):
 if Path(name).name!=name:raise ValueError('Unsafe file name')
 p=HERE/name
 if not p.exists() or expected and sha(p)!=expected:
  tmp=HERE/(name+'.download')
  print('Downloading',name,flush=True)
  with urllib.request.urlopen(BASE+name,timeout=120) as r,tmp.open('wb') as f:shutil.copyfileobj(r,f)
  if expected and sha(tmp)!=expected:raise ValueError('Hash mismatch '+name)
  tmp.replace(p)
 return p
manifest=json.loads(obtain('MANIFEST.json').read_text(encoding='utf-8'))
archive=HERE/manifest['archive']
with archive.open('wb') as f:
 for row in manifest['parts']:
  p=obtain(row['filename'],row['sha256'])
  if p.stat().st_size!=row['size']:raise ValueError('Size mismatch '+p.name)
  with p.open('rb') as src:shutil.copyfileobj(src,f)
if archive.stat().st_size!=manifest['archive_size'] or sha(archive)!=manifest['archive_sha256']:raise ValueError('Archive checksum mismatch')
out=HERE/'restored_assets';out.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
 for entry in z.infolist():
  dest=(out/entry.filename).resolve()
  if not dest.is_relative_to(out.resolve()):raise ValueError('Unsafe ZIP path')
 if z.testzip():raise ValueError('CRC mismatch')
 z.extractall(out)
for item in manifest['assets']:
 p=out/item['archive_path']
 if p.stat().st_size!=item['size'] or sha(p)!=item['sha256']:raise ValueError('Asset checksum mismatch '+item['id'])
print('Verified and restored to:',out)
print('Work-in-progress assets: read README and individual status before use.')
