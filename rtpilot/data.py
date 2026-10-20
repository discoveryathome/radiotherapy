"""Pinned source-data loading. No dose/metric routines shared with evaluator."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.io import loadmat
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
ANGLES = (0, 72, 144, 216, 288)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_files(root=ROOT):
    manifest = json.loads((root / 'data/manifest.json').read_text())
    for f in manifest['files']:
        if digest(root / f['path']) != f['sha256']:
            raise ValueError('Data SHA256 mismatch: ' + f['path'])
    return manifest

def load(root=ROOT):
    manifest = validate_files(root)
    blocks = [loadmat(root / f'data/raw/Gantry{a}_Couch0_D.mat')['D'].tocsc() for a in ANGLES]
    counts = [b.shape[1] for b in blocks]
    if counts != [98,70,90,90,70]:
        raise ValueError('Unexpected beam ordering or sizes')
    n = int(np.prod(manifest['grid_shape_ap_lr_si']))
    if any(b.shape[0] != n or not np.all(np.isfinite(b.data)) or np.any(b.data < 0) for b in blocks):
        raise ValueError('Invalid source matrix')
    vois = {}
    for name in ('OuterTarget','Core','BODY'):
        v = loadmat(root / f'data/raw/{name}_VOILIST.mat')['v'].ravel().astype(np.int64)-1
        if len(v) != len(np.unique(v)) or np.any(v < 0) or np.any(v >= n):
            raise ValueError('Invalid VOILIST')
        vois[name] = v
    vois['HealthyBody'] = np.setdiff1d(vois['BODY'], np.union1d(vois['OuterTarget'],vois['Core']))
    return sparse.hstack(blocks,format='csr'), vois, np.repeat(ANGLES,counts)

def write_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
