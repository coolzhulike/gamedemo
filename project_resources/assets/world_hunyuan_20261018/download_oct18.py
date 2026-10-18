#!/usr/bin/env python3
"""Download selected Oct18 archive groups at a pinned asset commit."""
import argparse
from pathlib import Path
from restore_verified_archive import restore
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ref',required=True);p.add_argument('--group',choices=['world','sources','authoring','all'],default='world');p.add_argument('--output',type=Path,default=Path('restored_oct18'));p.add_argument('--cache',type=Path,default=Path('oct18_download_cache'));a=p.parse_args()
if len(a.ref)!=40 or any(c not in '0123456789abcdef' for c in a.ref.lower()):p.error('--ref requires the full verified commit SHA')
base='https://raw.githubusercontent.com/coolzhulike/gamedemo/'+a.ref+'/project_resources/assets/world_hunyuan_20261018'
groups={'world':'world_oct18_manifest.json','sources':'original_sources_manifest.json','authoring':'authoring_oct18_manifest.json'}
for k,m in groups.items():
 if a.group in (k,'all'):restore(base,m,a.cache,a.output)
