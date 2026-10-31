"""Complete missing regional OSM extracts using bounded, cached tile requests."""
from run_discovery import *
for region in ['maricopa-az','south-central-tx']:
    output=CACHE/f'{region}.json'
    if output.exists():continue
    bounds=pq.read_table(DATA/f'{region}-census-tracts.parquet',columns=['bbox']).to_pylist()
    w=min(t['bbox']['xmin'] for t in bounds);s=min(t['bbox']['ymin'] for t in bounds);e=max(t['bbox']['xmax'] for t in bounds);n=max(t['bbox']['ymax'] for t in bounds)
    mx=(w+e)/2;my=(s+n)/2;tiles=[(w,s,mx,my),(mx,s,e,my),(w,my,mx,n),(mx,my,e,n)]
    combined={};complete=True;retrievals=[]
    for i,(tw,ts,te,tn) in enumerate(tiles):
        cache=CACHE/f'{region}.tile{i}.json'
        query=f'[out:json][timeout:75][date:"{DATE}"];nwr[amenity=fire_station]({ts},{tw},{tn},{te});out meta geom;'
        (CACHE/f'{region}.tile{i}.overpassql').write_text(query)
        if cache.exists():raw=cache.read_bytes();data=json.loads(raw)
        else:
            data=None
            for endpoint in ['https://overpass-api.de/api/interpreter','https://overpass.private.coffee/api/interpreter']:
                try:
                    req=urllib.request.Request(endpoint+'?'+urllib.parse.urlencode({'data':query}),headers={'User-Agent':'ZindiBiasDiscoveryResearch/1.0 (https://zindi.world/competitions/bias-bounty-mapping-equity-challenge)'})
                    with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
                    data=json.loads(raw)
                    if data.get('remark'):raise ValueError(data['remark'])
                    cache.write_bytes(raw);print('tile saved',region,i,len(data['elements']),flush=True);break
                except Exception as ex:print('tile failed',region,i,repr(ex),flush=True);data=None
            if data is None:complete=False;continue
        retrievals.append({'tile':i,'bbox':[tw,ts,te,tn],'sha256':hashlib.sha256(raw).hexdigest()})
        for el in data['elements']:combined[(el['type'],el['id'])]=el
    if complete:
        payload={'version':.6,'generator':'merged historical Overpass tiles','osm3s':{'historical_snapshot':DATE},'elements':[combined[k] for k in sorted(combined)]}
        raw=json.dumps(payload).encode();output.write_bytes(raw)
        (CACHE/f'{region}.retrieval.json').write_text(json.dumps({'method':'four cached tiles, deduplicated by object type/id','historical_snapshot':DATE,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':hashlib.sha256(raw).hexdigest(),'tiles':retrievals},indent=2))
        print('REGION COMPLETE',region,len(combined),flush=True)
    else:print('REGION INCOMPLETE',region,'complete tiles',len(retrievals),flush=True)
