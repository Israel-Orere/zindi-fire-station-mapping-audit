from run_discovery import *
targets=pd.read_csv(OUT/'exact_name_location_audit.csv',dtype={'GEOID':str});targets=targets[targets.distance_m>500]
result=[]
for region in targets.region.unique():
    candidates=targets[targets.region==region];ids=set(candidates.overture_id)
    pois={p['id']:p for p in pq.read_table(DATA/f'{region}-overture-pois.parquet',columns=['id','names','addresses','phones','sources','geometry']).to_pylist() if p['id'] in ids}
    sites={f['properties']['osm_id']:f for f in json.loads((CACHE/f'{region}.sites.geojson').read_text())['features']}
    for _,r in candidates.iterrows():
        p=pois[r.overture_id];g=from_wkb(p.pop('geometry'));p['geometry']=g.__geo_interface__
        f=sites[r.osm_id];obj={'name':r.osm_name,'region':region,'distance_km':r.distance_m/1000,'same_tract':bool(r.same_tract),'overture':p,'osm':f};result.append(obj)
        print(json.dumps({'name':r.osm_name,'distance_km':round(r.distance_m/1000,3),'same_tract':bool(r.same_tract),'osm_location':[f['properties']['lon'],f['properties']['lat']],'osm_tags':f['properties']['osm_tags'],'overture_location':[g.x,g.y],'overture_addresses':p['addresses']}),flush=True)
(ROOT/'work/recurrence_candidates.json').write_text(json.dumps(result,indent=2))
