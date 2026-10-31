from run_discovery import *
from concurrent.futures import ThreadPoolExecutor,as_completed
region='south-central-tx';output=CACHE/f'{region}.json'
if output.exists():raise SystemExit('Already complete')
bs=pq.read_table(DATA/f'{region}-census-tracts.parquet',columns=['bbox']).to_pylist()
w=min(t['bbox']['xmin'] for t in bs);s=min(t['bbox']['ymin'] for t in bs);e=max(t['bbox']['xmax'] for t in bs);n=max(t['bbox']['ymax'] for t in bs)
mx=(w+e)/2;my=(s+n)/2;tiles=[(w,s,mx,my),(mx,s,e,my),(w,my,mx,n),(mx,my,e,n)]
jobs=[];pieces=[]
for i,(tw,ts,te,tn) in enumerate(tiles):
    if (CACHE/f'{region}.tile{i}.json').exists():pieces.append((f'tile{i}',(tw,ts,te,tn)))
    else:
        xm=(tw+te)/2;ym=(ts+tn)/2
        for j,b in enumerate([(tw,ts,xm,ym),(xm,ts,te,ym),(tw,ym,xm,tn),(xm,ym,te,tn)]):jobs.append((f'tile{i}_sub{j}',b))
def fetch_piece(job):
    tag,(tw,ts,te,tn)=job;cache=CACHE/f'{region}.{tag}.json'
    query=f'[out:json][timeout:40][date:"{DATE}"];nwr[amenity=fire_station]({ts},{tw},{tn},{te});out meta geom;'
    (CACHE/f'{region}.{tag}.overpassql').write_text(query)
    if cache.exists():return job
    for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
        try:
            req=urllib.request.Request(endpoint+'?'+urllib.parse.urlencode({'data':query}),headers={'User-Agent':'ZindiBiasDiscoveryResearch/1.0'})
            raw=urllib.request.urlopen(req,timeout=50).read();d=json.loads(raw)
            if d.get('remark'):raise ValueError(d['remark'])
            cache.write_bytes(raw);print('saved',tag,len(d['elements']),flush=True);return job
        except Exception as ex:print('failed',tag,repr(ex),flush=True)
    return None
with ThreadPoolExecutor(max_workers=2) as pool:
    for f in as_completed([pool.submit(fetch_piece,j) for j in jobs]):
        result=f.result()
        if result:pieces.append(result)
if len(pieces)==len(jobs)+sum((CACHE/f'{region}.tile{i}.json').exists() for i in range(4)):
    combined={};retrievals=[]
    for tag,b in pieces:
        raw=(CACHE/f'{region}.{tag}.json').read_bytes();d=json.loads(raw)
        retrievals.append({'tile':tag,'bbox':b,'sha256':hashlib.sha256(raw).hexdigest()})
        for el in d['elements']:combined[(el['type'],el['id'])]=el
    payload={'version':.6,'generator':'merged historical Overpass subtiles','osm3s':{'historical_snapshot':DATE},'elements':[combined[k] for k in sorted(combined)]}
    raw=json.dumps(payload).encode();output.write_bytes(raw)
    (CACHE/f'{region}.retrieval.json').write_text(json.dumps({'method':'complete bbox partition using cached tiles and subtiles, deduplicated by type/id','historical_snapshot':DATE,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':hashlib.sha256(raw).hexdigest(),'tiles':retrievals},indent=2))
    print('REGION COMPLETE',len(combined),flush=True)
else:print('INCOMPLETE',len(pieces),'of',len(jobs)+1,'pieces',flush=True)
