import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from restore_originals import restore

class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache, self.out = self.root / "cache", self.root / "out"
        self.cache.mkdir()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("sources/male.glb", b"male-original")
            z.writestr("sources/female.glb", b"female-original")
            z.writestr("unrelated/motion.glb", b"do not restore")
        data = buffer.getvalue()
        parts = []
        for number, offset in enumerate(range(0, len(data), 100)):
            name = f"part{number}"
            blob = data[offset:offset+100]
            (self.cache / name).write_bytes(blob)
            parts.append(dict(filename=name, size=len(blob), sha256=hashlib.sha256(blob).hexdigest()))
        self.manifest = dict(parts=parts, assets=[
            dict(filename=f"{name}.glb", archive_path=f"sources/{name}.glb",
                 size=len(blob), sha256=hashlib.sha256(blob).hexdigest())
            for name, blob in [("male", b"male-original"), ("female", b"female-original")]
        ])
    def run_restore(self):
        restore(self.manifest, self.out, self.cache, offline=True)
    def test_only_originals_and_idempotent(self):
        self.run_restore()
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), ["female.glb", "male.glb"])
        self.run_restore()
    def test_missing_part(self):
        next(self.cache.iterdir()).unlink()
        with self.assertRaises(ValueError): self.run_restore()
        self.assertFalse(self.out.exists())
    def test_corrupt_part(self):
        next(self.cache.iterdir()).write_bytes(b"corrupt")
        with self.assertRaises(ValueError): self.run_restore()
        self.assertFalse(self.out.exists())
    def test_wrong_output_checksum(self):
        self.manifest["assets"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError): self.run_restore()
        self.assertFalse(self.out.exists())
    def test_protect_existing_file(self):
        self.out.mkdir()
        target = self.out / "male.glb"
        target.write_bytes(b"user data")
        with self.assertRaises(ValueError): self.run_restore()
        self.assertEqual(target.read_bytes(), b"user data")
    def test_reject_nonempty_directory(self):
        self.out.mkdir()
        (self.out / "unrelated.txt").write_text("preserve me")
        with self.assertRaises(ValueError): self.run_restore()
    def test_reject_output_traversal(self):
        self.manifest["assets"][0]["filename"] = "../escape.glb"
        with self.assertRaises(ValueError): self.run_restore()
        self.assertFalse((self.root / "escape.glb").exists())

if __name__ == "__main__":
    unittest.main()
