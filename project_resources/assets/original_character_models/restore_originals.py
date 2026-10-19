"""Restore only the two byte-identical, user-uploaded high-poly source GLBs."""
from pathlib import Path
import argparse
import bisect
import io
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def valid(path, row):
    return path.is_file() and path.stat().st_size == row["size"] and sha(path) == row["sha256"]

def restore(manifest, output, cache, offline=False):
    output, cache = Path(output), Path(cache)
    selected = manifest["assets"]
    allowed = {row["filename"] for row in selected}
    if output.exists() and (not output.is_dir() or any(p.name not in allowed for p in output.iterdir())):
        raise ValueError("Choose a new empty output directory (or one containing only verified originals)")
    # Never overwrite a different user file.
    for row in selected:
        dest = output / row["filename"]
        if dest.exists() and not valid(dest, row):
            raise ValueError("Existing output differs; choose another --output: " + str(dest))
    if all(valid(output / row["filename"], row) for row in selected):
        print("Both originals already verified:", output.resolve())
        return
    cache.mkdir(parents=True, exist_ok=True)
    archive_dir = HERE.parent / "characters_20261017" / "archive"
    def obtain(row):
        name = row["filename"]
        if Path(name).name != name:
            raise ValueError("Unsafe part name")
        for path in (archive_dir / name, cache / name):
            if valid(path, row):
                return path
        if offline:
            raise ValueError("Missing or corrupt archive part: " + name)
        destination = cache / name
        with tempfile.NamedTemporaryFile(dir=cache, delete=False) as tmp:
            temporary = Path(tmp.name)
            try:
                with urllib.request.urlopen(manifest["archive_base_url"] + name, timeout=120) as response:
                    shutil.copyfileobj(response, tmp)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            if not valid(temporary, row):
                raise ValueError("Part checksum mismatch: " + name)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination
    class PartsReader(io.RawIOBase):
        """Seekable ZIP reader; fetch only parts actually read by zipfile."""
        def __init__(self):
            self.position = 0
            self.offsets = [0]
            self.paths = {}
            for part in manifest["parts"]:
                self.offsets.append(self.offsets[-1] + part["size"])
        def seekable(self):
            return True
        def readable(self):
            return True
        def tell(self):
            return self.position
        def seek(self, offset, whence=0):
            position = offset if whence == 0 else self.position + offset if whence == 1 else self.offsets[-1] + offset
            if position < 0:
                raise ValueError("Negative seek")
            self.position = position
            return position
        def read(self, size=-1):
            remaining = max(0, self.offsets[-1] - self.position)
            size = remaining if size is None or size < 0 else min(size, remaining)
            chunks = []
            while size:
                index = bisect.bisect_right(self.offsets, self.position) - 1
                if index not in self.paths:
                    self.paths[index] = obtain(manifest["parts"][index])
                offset = self.position - self.offsets[index]
                amount = min(size, self.offsets[index + 1] - self.position)
                with self.paths[index].open("rb") as stream:
                    stream.seek(offset)
                    block = stream.read(amount)
                if len(block) != amount:
                    raise ValueError("Truncated part")
                chunks.append(block)
                self.position += amount
                size -= amount
            return b"".join(chunks)
    with tempfile.TemporaryDirectory(dir=cache) as work:
        staged = []
        with zipfile.ZipFile(PartsReader()) as bundle:
            for row in selected:
                if Path(row["filename"]).name != row["filename"]:
                    raise ValueError("Unsafe output name")
                info = bundle.getinfo(row["archive_path"])
                if info.file_size != row["size"]:
                    raise ValueError("Member size mismatch")
                dest = Path(work) / row["filename"]
                with bundle.open(info) as source, dest.open("wb") as target:
                    shutil.copyfileobj(source, target)
                if not valid(dest, row):
                    raise ValueError("Original checksum mismatch: " + row["filename"])
                staged.append((dest, row))
        output.mkdir(parents=True, exist_ok=True)
        for source, row in staged:
            dest = output / row["filename"]
            if not dest.exists():
                # Exclusive creation protects existing files, including concurrent writes.
                with dest.open("xb") as target, source.open("rb") as stream:
                    shutil.copyfileobj(stream, target)
            if not valid(dest, row):
                raise ValueError("Final output checksum mismatch: " + str(dest))
            print("Verified:", dest.resolve())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "models")
    parser.add_argument("--cache", type=Path, default=HERE / ".cache")
    parser.add_argument("--offline", action="store_true", help="Use only verified local archive parts")
    args = parser.parse_args()
    manifest = json.loads((HERE / "originals_manifest.json").read_text(encoding="utf-8"))
    restore(manifest, args.output, args.cache, args.offline)

if __name__ == "__main__":
    main()
