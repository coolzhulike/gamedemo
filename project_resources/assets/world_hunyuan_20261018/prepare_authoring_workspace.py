#!/usr/bin/env python3
"""Prepare portable copies of author scripts; does not execute Blender scripts.
Example: --authoring restored/authoring --sources restored/大世界建筑模型补齐 --output work
Original files remain untouched. Hardlinks avoid copying original GLBs where supported.
"""
from pathlib import Path
import argparse,shutil,os
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--authoring',type=Path,required=True);p.add_argument('--sources',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
if out.exists() and any(out.iterdir()):p.error('output must be a new/empty directory')
out.mkdir(parents=True,exist_ok=True)
shutil.copytree(a.authoring,out,dirs_exist_ok=True)
for path in out.rglob('*.py'):
 text=path.read_text();path.write_text(text.replace('/workspace/scratch/1d63341f978c',out.as_posix()))
dest=out/'assets_oct18/extracted/大世界建筑模型补齐';dest.mkdir(parents=True,exist_ok=True)
for source in a.sources.glob('*.glb'):
 try:os.link(source,dest/source.name)
 except OSError:shutil.copy2(source,dest/source.name)
print('Prepared',out,'— original inputs untouched; inspect scripts before running Blender')
