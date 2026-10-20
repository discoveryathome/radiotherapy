"""Restore pinned raw files from the original archive; reject changed bytes."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
import zipfile

root=Path(__file__).resolve().parents[1]
m=json.loads((root/'data/manifest.json').read_text())
with urllib.request.urlopen(m['archive_url'],timeout=60) as r:
    blob=r.read(30_000_001)
if len(blob)>30_000_000 or hashlib.sha256(blob).hexdigest()!=m['archive_sha256']:
    raise SystemExit('Archive size/hash mismatch; no files written')
with zipfile.ZipFile(io.BytesIO(blob)) as z:
    pending=[]
    for f in m['files']:
        dest=root/f['path'];data=z.read(dest.name)
        if hashlib.sha256(data).hexdigest()!=f['sha256']:
            raise SystemExit('Member hash mismatch; no files written')
        pending.append((dest,data))
    for dest,data in pending:
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
print('Restored',len(pending),'hash-verified original data files')
