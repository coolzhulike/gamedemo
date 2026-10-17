"""Stdlib-only review restore: Python 3.9+, no Blender/Godot required."""
import argparse, hashlib, json, re, shutil, stat, unicodedata
import urllib.parse, urllib.request, zipfile
from pathlib import Path

BRANCH = 'assets/characters-20261017-review-01'
REPOSITORY_PATH = 'project_resources/assets/characters_20261017/review_01'
ARCHIVE_NAME = 'delivery_review_01.zip'
DEFAULT = ('https://raw.githubusercontent.com/coolzhulike/gamedemo/refs/heads/'
           + BRANCH + '/' + REPOSITORY_PATH + '/')
BLOCK = 1024 * 1024
RESERVED = {'CON','PRN','AUX','NUL','CLOCK$','CONIN$','CONOUT$'}
RESERVED.update(p+n for p in ('COM','LPT') for n in '123456789\u00b9\u00b2\u00b3')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(BLOCK), b''): h.update(block)
    return h.hexdigest()

def safe_name(name, basename=False):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Unsafe path: '+repr(name))
    parts = name.split('/')
    if basename and len(parts) != 1: raise ValueError('Expected basename: '+repr(name))
    for part in parts:
        if (part in ('','.','..') or part.endswith(('.',' '))
            or any(ord(c)<32 or ord(c)==127 or c in '<>:"|?*' for c in part)
            or part.split('.')[0].rstrip(' ').upper() in RESERVED):
            raise ValueError('Unsafe Windows/archive path: '+repr(name))
    return name

def key(name):
    return unicodedata.normalize('NFC', name).casefold()

def check_path_set(names):
    seen, spellings = set(), {}
    for name in names:
        safe_name(name)
        if key(name) in seen: raise ValueError('Duplicate/case-equivalent path: '+name)
        seen.add(key(name)); parts = name.split('/')
        for i in range(1,len(parts)+1):
            prefix = '/'.join(parts[:i]); folded = key(prefix)
            if folded in spellings and spellings[folded] != prefix:
                raise ValueError('Ambiguous directory spelling: '+prefix)
            spellings[folded] = prefix
    for name in seen:
        parts = name.split('/')
        if any('/'.join(parts[:i]) in seen for i in range(1,len(parts))):
            raise ValueError('File/directory prefix collision: '+name)

def reject_links(path):
    # Inspect lexical ancestors before resolve follows a link.
    for part in [path, *path.parents]:
        try: item = part.lstat()
        except FileNotFoundError: continue
        if stat.S_ISLNK(item.st_mode) or getattr(item,'st_file_attributes',0)&0x400:
            raise ValueError('Symlink/junction/reparse refused: '+str(part))

def child(root, name):
    safe_name(name); result = root.joinpath(*name.split('/')); reject_links(result)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError('Escaped destination: '+name)
    return result

def validate_manifest(info):
    if (info.get('branch') != BRANCH or info.get('repository_path') != REPOSITORY_PATH
        or info.get('archive_filename') != ARCHIVE_NAME):
        raise ValueError('Manifest belongs to a different branch/path/archive')
    safe_name(info['archive_filename'], True)
    def valid_size_hash(entry):
        if type(entry.get('bytes')) is not int or entry['bytes'] < 0:
            raise ValueError('Invalid byte count')
        if not isinstance(entry.get('sha256'),str) or not re.fullmatch('[0-9a-fA-F]{64}',entry['sha256']):
            raise ValueError('Invalid SHA256')
    valid_size_hash({'bytes':info.get('archive_bytes'),'sha256':info.get('archive_sha256')})
    parts, files = info.get('parts'), info.get('files')
    if not isinstance(parts,list) or not parts or not isinstance(files,list) or not files:
        raise ValueError('Invalid/empty file or part list')
    for i,part in enumerate(parts,1):
        safe_name(part['filename'],True); valid_size_hash(part)
        if part['filename'] != f'delivery.zip.part{i:03d}' or not part['bytes']:
            raise ValueError('Part names must be unique and consecutively ordered')
    if sum(p['bytes'] for p in parts) != info['archive_bytes']:
        raise ValueError('Part sizes do not sum to archive size')
    for entry in files: safe_name(entry['path']); valid_size_hash(entry)
    check_path_set([entry['path'] for entry in files])
    return info

def matching(path,size,digest):
    reject_links(path)
    return path.is_file() and path.stat().st_size == size and sha(path).lower() == digest.lower()

def download_new(url,path):
    reject_links(path)
    # Exclusive create never truncates a cached/user file.
    with path.open('xb') as out, urllib.request.urlopen(url,timeout=60) as src:
        shutil.copyfileobj(src,out,BLOCK)

def obtain_archive(info,base,cache):
    for part in info['parts']:
        path = child(cache,part['filename'])
        if not path.exists(): download_new(base+part['filename'],path)
        if not matching(path,part['bytes'],part['sha256']):
            raise RuntimeError('Cached part failed SHA256/size; left untouched: '+str(path))
    combined = child(cache,ARCHIVE_NAME)
    if combined.exists():
        if not matching(combined,info['archive_bytes'],info['archive_sha256']):
            raise RuntimeError('Refusing to overwrite different cached archive: '+str(combined))
    else:
        with combined.open('xb') as dst:
            for part in info['parts']:
                with child(cache,part['filename']).open('rb') as src: shutil.copyfileobj(src,dst,BLOCK)
    if not matching(combined,info['archive_bytes'],info['archive_sha256']):
        raise RuntimeError('Combined archive failed SHA256/size')
    return combined

def verify_zip(z,info):
    expected = {e['path']:e for e in info['files']}; members = z.infolist()
    for member in members:
        # orig_filename retains NUL/truncation evidence hidden by filename.
        safe_name(member.orig_filename)
        if member.orig_filename != member.filename or member.is_dir():
            raise ValueError('Only exact regular-file ZIP members are supported')
        mode = stat.S_IFMT(member.external_attr >> 16)
        if mode not in (0,stat.S_IFREG) or member.flag_bits&1:
            raise ValueError('Link/special/encrypted ZIP member: '+member.filename)
    check_path_set([m.filename for m in members])
    if {m.filename for m in members} != set(expected):
        raise ValueError('ZIP members must match manifest files exactly')
    # Complete CRC and per-file SHA before writing any restored file.
    for member in members:
        entry = expected[member.filename]
        if member.file_size != entry['bytes']: raise ValueError('ZIP/manifest size mismatch')
        h = hashlib.sha256(); count = 0
        with z.open(member) as src:
            for block in iter(lambda:src.read(BLOCK),b''): count += len(block); h.update(block)
        # zipfile checks member CRC on complete consumption.
        if count != entry['bytes'] or h.hexdigest().lower() != entry['sha256'].lower():
            raise ValueError('ZIP member SHA256/size mismatch: '+member.filename)
    return expected

def restore_archive(combined,info,target):
    validate_manifest(info); target = target.absolute(); reject_links(target)
    with zipfile.ZipFile(combined) as z:
        expected = verify_zip(z,info); pending = []
        for name,entry in expected.items():
            path = child(target,name)
            if path.exists():
                if not matching(path,entry['bytes'],entry['sha256']):
                    raise RuntimeError('Refusing to overwrite different existing file: '+str(path))
            else: pending.append(name)
        # Preflight all directory/file conflicts before the first output write.
        for name in pending:
            for parent in child(target,name).parents:
                if parent.exists() and not parent.is_dir():
                    raise RuntimeError('Existing file blocks output directory: '+str(parent))
                if parent == target: break
        target.mkdir(parents=True,exist_ok=True)
        for name in pending:
            path = child(target,name); path.parent.mkdir(parents=True,exist_ok=True); reject_links(path)
            with path.open('xb') as dst,z.open(name) as src: shutil.copyfileobj(src,dst,BLOCK)
    for name,entry in expected.items():
        if not matching(child(target,name),entry['bytes'],entry['sha256']):
            raise RuntimeError('Restored asset failed SHA256/size: '+name)
    return len(expected)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',default=DEFAULT)
    p.add_argument('--output',type=Path,default=Path('restored_character_review_01'))
    p.add_argument('--cache',type=Path,default=Path(__file__).resolve().parent/'review_01_downloads')
    args = p.parse_args(); base = args.base_url.rstrip('/')+'/'
    if urllib.parse.urlparse(base).scheme not in ('https','file'):
        raise ValueError('Use HTTPS, or file:// for an explicit offline mirror')
    cache = args.cache.absolute(); target = args.output.absolute()
    reject_links(cache); reject_links(target); cache = cache.resolve(); target = target.resolve()
    if cache == target or cache.is_relative_to(target) or target.is_relative_to(cache):
        raise ValueError('Keep download cache and restored output in separate directories')
    cache.mkdir(parents=True,exist_ok=True); manifest = child(cache,'MANIFEST.json')
    if not manifest.exists(): download_new(base+'MANIFEST.json',manifest)
    info = validate_manifest(json.loads(manifest.read_text(encoding='utf-8')))
    count = restore_archive(obtain_archive(info,base,cache),info,target)
    print(f'All parts, ZIP CRCs and {count} restored SHA256 files verified. Read {target/"DELIVERY_REPORT.md"}')

if __name__ == '__main__': main()

