"""Verify frozen evidence against explicitly pinned historical entry versions.

Both the live replacement and the historical bytes must match the recorded hashes.
A future edit cannot silently pass by falling back to an old snapshot.
"""
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ALLOWED=('AGENTS.md', 'DISCOVERY.md', 'README.md', 'discover.json', 'discover/catalog.json')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve(name, expected, root=ROOT):
    mapping=json.loads((root/'research/participation-20261022/snapshots.json').read_text())
    records=mapping.get('versions',{})
    if set(records)-set(ALLOWED):
        raise ValueError('Undeclared participation snapshot path')
    record=records.get(name,{}).get(expected)
    if record is None:
        return root/name
    live=root/name
    if digest(live)!=record['current_sha256']:
        raise ValueError('Changed current participation document: '+name)
    want='research/participation-20261022/historical/'+expected+'/'+name
    if record['snapshot']!=want:
        raise ValueError('Invalid participation snapshot path')
    snapshot=root/want
    if digest(snapshot)!=expected:
        raise ValueError('Changed historical participation document: '+name)
    return snapshot

def check_manifest(path):
    manifest=json.loads(path.read_text())
    for name,expected in manifest['files'].items():
        if digest(resolve(name,expected))!=expected:
            raise ValueError('Changed evidence: '+name)
    print('PASS',len(manifest['files']),'historical evidence hashes; participation open, acceptance requires review')

if __name__=='__main__':
    mapping=json.loads((HERE/'snapshots.json').read_text())
    for name,versions in mapping['versions'].items():
        for expected in versions: resolve(name,expected)
    print('PASS',sum(map(len,mapping['versions'].values())),'pinned participation snapshots')
