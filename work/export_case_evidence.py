from run_discovery import *
from shapely.geometry import shape
ids={'porum':'b8dbd5fb-9deb-4e96-92ee-918971bdbeb5','webbers_falls':'28e96c4a-fec6-4715-baef-e40708362cfd'}
pois=pq.read_table(DATA/'eastern-ok-overture-pois.parquet').to_pylist()
sites=json.loads((CACHE/'eastern-ok.sites.geojson').read_text())['features']
tracts=json.loads((CACHE/'eastern-ok.tracts.json').read_text());geos=[shape(t['geometry']) for t in tracts];tree=STRtree(geos)
result={}
for label,id in ids.items():
    p=next(p for p in pois if p['id']==id);g=from_wkb(p.pop('geometry'));p['geometry']=g.__geo_interface__
    members=tree.query(g,predicate='intersects');p['mapped_GEOID']=tracts[int(members[0])]['GEOID'] if len(members) else None
    target='Porum Volunteer Fire Department' if label=='porum' else 'Webbers Falls Volunteer Fire Department'
    osm=next(s for s in sites if s['properties']['osm_name']==target)
    result[label]={'overture':p,'osm':osm,'point_distance_m':distance(Point(osm['properties']['lon'],osm['properties']['lat']),g,osm['properties']['lat'])}
    print(label,{k:p.get(k) for k in ['id','addresses','phones','websites','sources','mapped_GEOID']},result[label]['point_distance_m'],flush=True)
(OUT/'named_case_evidence.json').write_text(json.dumps(result,indent=2))
