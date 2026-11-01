"""Download only organizer-provided inputs and enforce their recorded hashes."""
from pathlib import Path
import argparse, hashlib, json, urllib.request
p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,default=Path('data'));a=p.parse_args()
a.data_dir.mkdir(parents=True,exist_ok=True)
manifest=json.loads((Path(__file__).parent/'input_manifest.json').read_text())
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
for item in manifest:
    path=a.data_dir/item['name']
    if path.exists() and sha(path)==item['sha256']:continue
    temp=path.with_suffix(path.suffix+'.part')
    print('Downloading',item['name'],flush=True)
    with urllib.request.urlopen(item['url'],timeout=120) as src,temp.open('wb') as dst:
        while b:=src.read(1024*1024):dst.write(b)
    if temp.stat().st_size!=item['bytes'] or sha(temp)!=item['sha256']:
        raise RuntimeError('Source changed or download incomplete: '+item['name'])
    temp.replace(path)
print('All 15 input files match the recorded original bytes.')
