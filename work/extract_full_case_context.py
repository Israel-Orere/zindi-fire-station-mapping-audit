from run_discovery import *
from shapely.geometry import shape,box
cases=json.loads((ROOT/'work/recurrence_candidates.json').read_text())
base=ROOT/'work/original_ten_cases.json'
if not base.exists():base.write_text(json.dumps(cases,indent=2))
result=[]
for region in sorted(set(c['region'] for c in cases)):
    pois=pq.read_table(DATA/f'{region}-overture-pois.parquet',columns=['id','names','addresses','categories','confidence','sources','geometry']).to_pylist()
    geoms=[from_wkb(p.pop('geometry')) for p in pois];tree=STRtree(geoms)
    for c in [c for c in cases if c['region']==region]:
        context={**c,'nearby':{}}
        for label,g in [('osm_site',shape(c['osm']['geometry'])),('overture_site',shape(c['overture']['geometry']))]:
            records=[]
            for j in tree.query(g.buffer(.004)):
                p=pois[j];dist=distance(g,geoms[j],c['osm']['properties']['lat'])
                if dist<=350:
                    records.append({'id':p['id'],'name':(p['names'] or {}).get('primary'),'categories':p['categories'],'addresses':p['addresses'],'confidence':p['confidence'],'sources':p['sources'],'distance_from_site_m':dist,'geometry':geoms[j].__geo_interface__})
            context['nearby'][label]=sorted(records,key=lambda p:p['distance_from_site_m'])
        result.append(context)
        print(json.dumps({'name':c['name'],'near_osm_count':len(context['nearby']['osm_site']),'fire_related':[(p['name'],p['categories'],round(p['distance_from_site_m'])) for p in context['nearby']['osm_site'] if re.search('fire|rescue|calfire',p['name'] or '',re.I)]}),flush=True)
(ROOT/'work/full_case_context.json').write_text(json.dumps(result,indent=2))
