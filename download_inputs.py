from pathlib import Path
import json,urllib.request,hashlib
r=Path(__file__).resolve().parent
d=r/'data';d.mkdir(exist_ok=True)
for item in json.loads((r/'outputs/input_manifest.json').read_text()):
 p=d/item['name']
 if not p.exists():
  print('Downloading',item['name'],flush=True)
  urllib.request.urlretrieve(item['url'],p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],('Input changed',p)
