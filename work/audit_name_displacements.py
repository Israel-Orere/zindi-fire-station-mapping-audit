from run_discovery import *
from shapely.geometry import shape
rows=[]
for region in REGIONS:
    path=OUT/f'{region}_facility_audit.csv'
    if not path.exists():continue
    d=pd.read_csv(path,dtype={'GEOID':str},keep_default_na=False);d=d[(d.facility_type=='fire')&(d.osm_name!='')].copy();d['key']=d.osm_name.map(norm)
    # Require unique normalized names on both sides; avoids attributing a multi-station department to one site.
    d=d[(d.key.str.len()>=6)&(~d.key.duplicated(keep=False))]
    d=d[d.osm_name.map(lambda s:bool(re.sub(r'(fire|station|district|department|volunteer|county|city|of|no|number|rescue|fes|[0-9# .-])','',s.lower()).strip()))]
    names=collections.defaultdict(list);keys=set(d.key)
    for p in pq.read_table(DATA/f'{region}-overture-pois.parquet',columns=['id','names','categories','confidence','sources','geometry']).to_pylist():
        nm=(p.get('names') or {}).get('primary','') or '';key=norm(nm)
        if key in keys:names[key].append(p)
    tr=json.loads((CACHE/f'{region}.tracts.json').read_text());tg=[shape(t['geometry']) for t in tr];ttree=STRtree(tg)
    for _,r in d.iterrows():
        if len(names[r.key])!=1:continue
        p=names[r.key][0];g=from_wkb(p['geometry']);dist=distance(Point(r.lon,r.lat),g,r.lat)
        ti=ttree.query(g,predicate='intersects');dest=tr[int(ti[0])] if len(ti) else {}
        rows.append({'region':region,'GEOID':r.GEOID,'ur_class':r.ur_class,'osm_id':r.osm_id,'osm_name':r.osm_name,'overture_id':p['id'],'overture_name':p['names']['primary'],'distance_m':dist,'same_tract':dest.get('GEOID')==r.GEOID,'destination_GEOID':dest.get('GEOID'),'destination_ur_class':dest.get('ur_class'),'overture_confidence':p['confidence'],'overture_primary':(p['categories'] or {}).get('primary'),'source':';'.join(sorted(set(s.get('dataset','') for s in p['sources'] or [] if not s.get('property'))))})
    print('name audit',region,'exact unique pairs',sum(r['region']==region for r in rows),flush=True)
f=pd.DataFrame(rows);f.to_csv(OUT/'exact_name_location_audit.csv',index=False)
print(f[f.distance_m>500].sort_values('distance_m',ascending=False).head(15).to_string(index=False),flush=True)
