from run_discovery import *
from concurrent.futures import ThreadPoolExecutor
dest=ROOT/'work/osm_history';dest.mkdir(exist_ok=True)
cases=json.loads((ROOT/'work/recurrence_candidates.json').read_text())
def job(c):
    ident=c['osm']['properties']['osm_id'];p=dest/(ident.replace('/','_')+'.json');url='https://api.openstreetmap.org/api/0.6/'+ident+'/history.json'
    try:
        if not p.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'ZindiBiasDiscoveryResearch/1.0 (https://zindi.world/competitions/bias-bounty-mapping-equity-challenge)'})
            with urllib.request.urlopen(req,timeout=45) as r:raw=r.read()
            p.write_bytes(raw)
        else:raw=p.read_bytes()
        data=json.loads(raw);versions=[{'version':e.get('version'),'timestamp':e.get('timestamp'),'changeset':e.get('changeset'),'tags':e.get('tags',{}),'lon':e.get('lon'),'lat':e.get('lat')} for e in data['elements']]
        result={'name':c['name'],'osm_id':ident,'url':url,'versions':versions,'status':'saved','sha256':hashlib.sha256(raw).hexdigest()}
    except Exception as ex:result={'name':c['name'],'osm_id':ident,'url':url,'status':'failed','error':repr(ex)}
    print(json.dumps(result),flush=True);return result
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(job,cases))
(dest/'review_history.json').write_text(json.dumps(results,indent=2))
