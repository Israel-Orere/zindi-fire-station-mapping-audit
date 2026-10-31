from run_discovery import *
def load_audits():
    frames=[]
    for region in REGIONS:
        p=OUT/f'{region}_facility_audit.csv'
        if p.exists():frames.append(pd.read_csv(p,dtype={'GEOID':str},keep_default_na=False))
    return pd.concat(frames,ignore_index=True)
d=load_audits()
tracts=[]
for region in d.region.unique():
    st=pd.read_csv(DATA/f'{region}-strata-tract-table.csv',dtype={'GEOID':str})
    st['region']=region;tracts.append(st)
t=pd.concat(tracts,ignore_index=True)
count=d.groupby(['GEOID','facility_type']).size().unstack(fill_value=0).rename(columns={'fire':'osm_fire','school':'osm_school'})
t=t.merge(count,on='GEOID',how='left').fillna({'osm_fire':0,'osm_school':0})
rates=d.groupby('GEOID').agg(sites=('osm_id','size'),retained=('compatible_100m','sum'))
t=t.merge(rates,on='GEOID',how='left')
features=['pop_total','osm_fire','osm_school','usfs_Exposure_mean','epht_heat_days_annual','usdm_summer_dsci']
def pair(target):
    rr=t[t.GEOID==target].iloc[0]
    pool=t[(t.region==rr.region)&(t.ur_class=='Urban')&(t.osm_fire==rr.osm_fire)&(t.pop_total>=rr.pop_total/1.3)&(t.pop_total<=rr.pop_total*1.3)].copy()
    if not len(pool):return None
    dist=(np.log1p(pool.pop_total)-math.log1p(rr.pop_total))**2
    for feat in features[3:]:
        if not pd.isna(rr[feat]):
            scale=t.loc[t.region==rr.region,feat].std()
            if scale>0:dist+=((pool[feat]-rr[feat])/scale).fillna(3)**2
    pool['matching_distance']=np.sqrt(dist)
    return pool.sort_values(['matching_distance','GEOID']).iloc[0]
for target in ['40101001502','40117957500','40101001501']:
    r=t[t.GEOID==target].iloc[0];p=pair(target)
    print('PAIR',target,{k:r[k] for k in ['pop_total','osm_fire','osm_school']},None if p is None else {k:p[k] for k in ['GEOID','pop_total','osm_fire','osm_school','matching_distance']},flush=True)
    if p is not None:print(d[(d.GEOID==p.GEOID)&(d.facility_type=='fire')][['osm_name','lon','lat','compatible_100m']].to_dict('records'),flush=True)
# Aggregate descriptive comparison; no population weighting, OSM is the denominator.
metrics=['compatible_50m','compatible_100m','compatible_200m','primary_100m']
if 'identity_candidate' in d and d.identity_candidate.isin([True,False]).all():metrics+=['identity_candidate']
s=d.groupby(['region','ur_class','facility_type']).agg(sites=('osm_id','size'),**{m:(m,'mean') for m in metrics}).reset_index()
s.to_csv(OUT/'retention_by_region.csv',index=False)
d.to_csv(OUT/'facility_audit.csv',index=False)
t.drop(columns=['geometry','bbox'],errors='ignore').to_csv(ROOT/'work/tract_analysis.csv',index=False)
print(s.to_string(index=False),flush=True)
