"""Historical OSM comparison for Best Bias Discovery only; no scored predictions."""
from pathlib import Path
import sys,json,urllib.request,urllib.parse,hashlib,time,math,csv,re,difflib,collections,os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from shapely import from_wkb,Point,Polygon,LineString,STRtree
ROOT=Path(__file__).resolve().parent.parent
DATA=Path(os.environ.get('ZINDI_DATA_DIR',str(ROOT/'data')))
CACHE=ROOT/'work/osm';CACHE.mkdir(exist_ok=True)
OUT=ROOT/'outputs';OUT.mkdir(exist_ok=True)
REGIONS=['eastern-ok','eastern-wa','maricopa-az','northern-ca','south-central-tx']
DATE='2026-08-01T00:00:00Z'
TYPES={'fire':{'fire_department'},'school':{'elementary_school','middle_school','high_school','school','private_school','public_school'}}
def fetch(region,bbox):
    w,s,e,n=bbox
    clauses=f'nwr[amenity=fire_station]({s},{w},{n},{e});'
    if region=='eastern-ok':clauses+=f'nwr[amenity=school]({s},{w},{n},{e});'
    q=f'[out:json][timeout:90][date:"{DATE}"];({clauses});out meta geom;'
    p=CACHE/f'{region}.json';(CACHE/f'{region}.overpassql').write_text(q)
    if p.exists():return json.loads(p.read_text(encoding='utf-8'))
    for endpoint in ['https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter']:
        try:
            req=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':q}).encode(),headers={'User-Agent':'ZindiBiasDiscoveryResearch/1.0'})
            with urllib.request.urlopen(req,timeout=110) as r:raw=r.read()
            d=json.loads(raw)
            if d.get('remark'):raise ValueError(d['remark'])
            p.write_bytes(raw)
            (CACHE/f'{region}.retrieval.json').write_text(json.dumps({'url':endpoint,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'historical_snapshot':DATE,'sha256':hashlib.sha256(raw).hexdigest(),'bbox':bbox},indent=2))
            print('downloaded',region,len(d['elements']),'OSM objects',flush=True);return d
        except Exception as ex:print('fetch failed',region,endpoint,repr(ex),flush=True)
    raise RuntimeError('All OSM endpoints failed for '+region)
def geom(el):
    if el['type']=='node':return Point(el['lon'],el['lat'])
    if el.get('geometry'):
        pts=[(p['lon'],p['lat']) for p in el['geometry'] if p]
        if len(pts)>=4 and pts[0]==pts[-1]:
            g=Polygon(pts)
            return g if g.is_valid else g.buffer(0)
        if len(pts)>=2:return LineString(pts)
    # Multipolygon members: exterior rings are enough for this point matching audit.
    polys=[]
    for m in el.get('members',[]):
        pts=[(p['lon'],p['lat']) for p in m.get('geometry',[]) if p]
        if m.get('role')=='outer' and len(pts)>=4 and pts[0]==pts[-1]:polys.append(Polygon(pts))
    if polys:return max(polys,key=lambda p:p.area)
    if el.get('bounds'):
        b=el['bounds'];return Point((b['minlon']+b['maxlon'])/2,(b['minlat']+b['maxlat'])/2)
    return None
def norm(s):return re.sub('[^a-z0-9]','',s.lower().replace('volunteer','').replace('department','').replace('school',''))
def distance(a,b,lat):
    # Local equirectangular coordinates in metres. Error negligible for <=300 m matching.
    from shapely.ops import transform
    c=math.cos(math.radians(lat)); fn=lambda x,y,z=None:(np.asarray(x)*111320*c,np.asarray(y)*111320)
    return transform(fn,a).distance(transform(fn,b))
def run(region):
    ts=pq.read_table(DATA/f'{region}-census-tracts.parquet').to_pylist()
    tgeoms=[from_wkb(t.pop('geometry')) for t in ts];tree=STRtree(tgeoms)
    bounds=(min(g.bounds[0] for g in tgeoms),min(g.bounds[1] for g in tgeoms),max(g.bounds[2] for g in tgeoms),max(g.bounds[3] for g in tgeoms))
    raw=fetch(region,bounds)
    pois=pq.read_table(DATA/f'{region}-overture-pois.parquet',columns=['id','names','categories','sources','confidence','geometry']).to_pylist()
    pgeoms=[from_wkb(p.pop('geometry')) for p in pois];ptree=STRtree(pgeoms)
    for t in ts:t['region']=region
    rows=[];geos=[]
    for el in raw['elements']:
        tags=el.get('tags',{});typ={'fire_station':'fire','school':'school'}.get(tags.get('amenity'))
        if not typ or tags.get('disused')=='yes' or tags.get('abandoned')=='yes':continue
        g=geom(el)
        if g is None or g.is_empty:continue
        p=g.representative_point();ti=tree.query(p,predicate='intersects')
        if not len(ti):continue
        t=ts[int(ti[0])];name=tags.get('name','')
        # Collapse multiple OSM representations of the same named campus/station.
        duplicate=None
        for j in range(len(rows)-1,-1,-1):
            r=rows[j]
            if r['facility_type']!=typ or abs(r['lat']-p.y)>.003:continue
            names_agree=bool(name and r['osm_name'] and norm(name)==norm(r['osm_name']))
            one_unnamed=not name or not r['osm_name']
            if (g.intersects(geos[j]) and (names_agree or one_unnamed)) or (names_agree and distance(g,geos[j],p.y)<60):
                duplicate=j;break
        if duplicate is not None:
            rows[duplicate]['osm_duplicates']+=';'+el['type']+'/'+str(el['id']);continue
        r={'region':region,'GEOID':t['GEOID'],'ur_class':t['ur_class'],'pct_urban':t['pct_urban'],'facility_type':typ,'osm_id':el['type']+'/'+str(el['id']),'osm_name':name,'osm_version':el.get('version'),'osm_timestamp':el.get('timestamp'),'osm_duplicates':'','lon':p.x,'lat':p.y,'geometry_type':g.geom_type,'gnis_tag':any(k.startswith('gnis:') for k in tags),'osm_source':tags.get('source',''),'osm_tags':json.dumps(tags,sort_keys=True)}
        candidates=[]
        for j in ptree.query(g.buffer(.004)):
            p2=pois[j];dist=distance(g,pgeoms[j],p.y)
            if dist>350:continue
            cats=p2.get('categories') or {};primary=cats.get('primary') or '';alts=cats.get('alternate') or []
            nm=(p2.get('names') or {}).get('primary','') or ''
            similarity=difflib.SequenceMatcher(None,norm(name),norm(nm)).ratio() if name and nm else 0
            candidates.append((dist,int(j),primary,bool(set([primary]+alts)&TYPES[typ]),similarity,nm))
        compatible=sorted([x for x in candidates if x[3]])
        best=compatible[0] if compatible else None
        r['compatible_distance_m']=best[0] if best else None
        for radius in [50,100,200]:r[f'compatible_{radius}m']=bool(best and best[0]<=radius)
        r['primary_100m']=any(x[0]<=100 and x[2] in TYPES[typ] for x in candidates)
        same_name=sorted([x for x in candidates if x[4]>=.65],key=lambda x:(-x[4],x[0]))
        chosen=best if best and best[0]<=100 else same_name[0] if same_name else None
        if chosen:
            dist,j,primary,compat,sim,nm=chosen
            r.update(overture_id=pois[j]['id'],overture_name=nm,overture_primary=primary,overture_match_distance_m=dist,name_similarity=sim,overture_sources=';'.join(sorted(set(s.get('dataset','') for s in pois[j].get('sources') or [] if s.get('property') in ['',None]))))
        else:r.update(overture_id='',overture_name='',overture_primary='',overture_match_distance_m=None,name_similarity=None,overture_sources='')
        r['named_compatible_350m']=any(x[3] and x[4]>=.8 for x in candidates)
        r['identity_candidate']=r['compatible_100m'] or r['named_compatible_350m']
        r['status']='compatible place within 100m' if r['compatible_100m'] else 'compatible named place within 350m' if r['named_compatible_350m'] else 'similar name: review category/location' if chosen else 'no compatible place within 100m'
        rows.append(r);geos.append(g)
    # Evidence geometries for maps and review.
    (CACHE/f'{region}.sites.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','properties':r,'geometry':g.__geo_interface__} for r,g in zip(rows,geos)]}))
    df=pd.DataFrame(rows);df.to_csv(OUT/f'{region}_facility_audit.csv',index=False)
    for t,g in zip(ts,tgeoms):t['geometry']=g.__geo_interface__;t.pop('bbox',None)
    (CACHE/f'{region}.tracts.json').write_text(json.dumps(ts))
    print('AUDIT',region,len(rows),df.groupby(['ur_class','facility_type']).compatible_100m.agg(['count','mean']).to_dict(),flush=True)
    return df
if __name__=='__main__':
    dfs=[]
    for r in (sys.argv[1:] or [r for r in REGIONS if (CACHE/f'{r}.json').exists()] or REGIONS):
        try:dfs.append(run(r))
        except Exception as ex:print('REGION UNAVAILABLE',r,repr(ex),flush=True)
    d=pd.concat(dfs,ignore_index=True);d.to_csv(OUT/'facility_audit.csv',index=False)
    s=d.groupby(['region','ur_class','facility_type']).agg(sites=('osm_id','size'),retained=('compatible_100m','sum'),rate=('compatible_100m','mean'),rate_50m=('compatible_50m','mean'),rate_200m=('compatible_200m','mean')).reset_index();s.to_csv(OUT/'retention_by_region.csv',index=False)
    print(s.to_string(index=False),flush=True)
