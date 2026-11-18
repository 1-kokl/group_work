"""Verify and restore the source snapshot used for the measured baseline."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from common import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
archive = ROOT / "evidence/week9/baseline-source.zip"
manifest = json.loads((ROOT / "evidence/week9/baseline-source.json").read_text(encoding="utf-8"))
if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["zip_sha256"]:
    raise SystemExit("Source archive checksum mismatch")
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
with ZipFile(archive) as source:
    for name in source.namelist():
        target = (output / name).resolve()
        if not target.is_relative_to(output):
            raise SystemExit("Unsafe archive member")
    source.extractall(output)
for name, expected in manifest["files"].items():
    if hashlib.sha256((output / name).read_bytes()).hexdigest() != expected:
        raise SystemExit("Restored source checksum mismatch: "+name)
print("Verified source snapshot:", output)
