from run_discovery import *
from scipy.optimize import linear_sum_assignment
from scipy.stats import t as student_t
protocol=json.loads((ROOT/'work/equity_analysis_protocol.json').read_text())
RNG=np.random.default_rng(20261024)
regions=[r for r in REGIONS if (OUT/f'{r}_facility_audit.csv').exists()]
frames=[];strata=[]
for region in regions:
    a=pd.read_csv(OUT/f'{region}_facility_audit.csv',dtype={'GEOID':str},keep_default_na=False);frames.append(a[a.facility_type=='fire'].copy())
    s=pd.read_csv(DATA/f'{region}-strata-tract-table.csv',dtype={'GEOID':str}).copy();s['region']=region
    # Need thresholds use all supplied tracts and are independent of representation outcomes.
    s['wildfire_threshold']=s.usfs_Exposure_mean.quantile(.75)
    s['high_wildfire']=np.where(s.usfs_Exposure_mean.notna(),np.where(s.usfs_Exposure_mean>=s.wildfire_threshold,'High wildfire exposure','Other wildfire exposure'),'Unknown wildfire exposure')
    for col,key in [('usfs_Exposure_mean','wildfire_rank'),('epht_heat_days_annual','heat_rank'),('usdm_summer_dsci','drought_rank'),('cvi_overall','cvi_rank')]:s[key]=s[col].rank(pct=True)
    s['svi_band']=pd.cut(s.svi_overall,[-np.inf,.25,.75,np.inf],labels=['Low SVI','Intermediate SVI','High SVI']).astype('string').fillna('Unknown SVI')
    s['tribal_band']=np.select([s.tribal_pct.isna(),s.tribal_pct>=.5,s.tribal_pct>0],['Unknown overlap','At least 50% tribal-area overlap','Some overlap below 50%'],default='No tribal-area overlap')
    s['tribal_legal_band']=np.select([s.tribal_legal_pct.isna(),s.tribal_legal_pct>=.5,s.tribal_legal_pct>0],['Unknown overlap','At least 50% legal-area overlap','Some legal-area overlap below 50%'],default='No legal-area overlap')
    s['county']=s.GEOID.str[:5];s['tract_rurality']=s.ur_class.fillna('Unknown')
    strata.append(s)
s=pd.concat(strata,ignore_index=True);f=pd.concat(frames,ignore_index=True)
assert s.GEOID.is_unique and f.osm_id.is_unique
fields=['GEOID','county','pop_total','ALAND','svi_overall','svi_socioeconomic','svi_household','svi_minority','svi_housing_transport','svi_rank_universe','svi_year','svi_band','cvi_overall','cvi_rank','cvi_source_vintage','tribal_band','tribal_legal_band','tribal_pct','tribal_legal_pct','tribal_stat_pct','aiannh_name','aiannh_kind','wildfire_rank','heat_rank','drought_rank','high_wildfire','wildfire_threshold','usfs_Exposure_mean','usfs_BP_mean','epht_heat_days_annual','usdm_summer_dsci']
f=f.merge(s[fields],on='GEOID',validate='many_to_one')
f['rural']=f.ur_class.eq('Rural');f['polygon']=f.geometry_type.isin(['Polygon','MultiPolygon'])
f['last_edit_year']=pd.to_datetime(f.osm_timestamp,utc=True).dt.year
f['record_age_years']=(pd.Timestamp(DATE)-pd.to_datetime(f.osm_timestamp,utc=True)).dt.total_seconds()/(365.25*86400)
f['named']=f.osm_name.ne('');f['numbered_station']=f.osm_tags.map(lambda v:bool(json.loads(v).get('ref')) or bool(re.search(r'(?:station|sta\.?|#)\s*\d+',json.loads(v).get('name',''),re.I)))
for col in ['gnis_tag','compatible_50m','compatible_100m','compatible_200m','primary_100m']:
    assert f[col].isin([True,False]).all(),col
tract=f.groupby('GEOID').agg(osm_fire_sites=('osm_id','size'),matched_50m=('compatible_50m','sum'),matched_100m=('compatible_100m','sum'),matched_200m=('compatible_200m','sum'),polygon_share=('polygon','mean'),gnis_share=('gnis_tag','mean'),mean_record_age=('record_age_years','mean')).reset_index()
t=s.merge(tract,on='GEOID',how='left',validate='one_to_one');t['osm_fire_sites']=t.osm_fire_sites.fillna(0).astype(int)
for radius in [50,100,200]:t[f'correspondence_{radius}m']=t[f'matched_{radius}m']/t.osm_fire_sites.replace(0,np.nan)
t['no_local_match_100m']=t.osm_fire_sites.gt(0)&t.matched_100m.eq(0)
t['one_mapped_site_unmatched']=t.osm_fire_sites.eq(1)&t.matched_100m.eq(0)
f['osm_fire_sites']=f.GEOID.map(t.set_index('GEOID').osm_fire_sites)
def record_rates(frame,group,analysis):
    rows=[]
    for keys,g in frame.groupby(group,dropna=False,observed=True):
        if not isinstance(keys,tuple):keys=(keys,)
        row={'analysis':analysis,**dict(zip(group,keys)),'sites':len(g),'tracts':g.GEOID.nunique(),'counties':g.county.nunique(),'sparse':len(g)<20 or g.GEOID.nunique()<10}
        for r in [50,100,200]:row[f'matched_{r}m']=int(g[f'compatible_{r}m'].sum());row[f'rate_{r}m']=float(g[f'compatible_{r}m'].mean())
        rows.append(row)
    return rows
groups=[]
for group,name in [(['region','ur_class'],'rurality'),(['region','ur_class','svi_band'],'rurality_svi'),(['region','ur_class','high_wildfire'],'rurality_wildfire'),(['region','ur_class','svi_band','high_wildfire'],'rurality_svi_wildfire'),(['region','ur_class','tribal_band'],'rurality_tribal'),(['region','ur_class','tribal_legal_band'],'rurality_legal_tribal')]:groups+=record_rates(f,group,name)
pd.DataFrame(groups).to_csv(OUT/'equity_subgroup_rates.csv',index=False)
pooled=[]
for group,name in [(['ur_class'],'rurality'),(['ur_class','svi_band'],'rurality_svi'),(['ur_class','high_wildfire'],'rurality_wildfire'),(['ur_class','svi_band','high_wildfire'],'rurality_svi_wildfire'),(['ur_class','tribal_band'],'rurality_tribal')]:pooled+=record_rates(f,group,name)
pd.DataFrame(pooled).to_csv(OUT/'equity_pooled_subgroup_rates.csv',index=False)
# Rural/urban gaps under independently defined map-quality and weighting restrictions.
reviewed=set(json.loads((OUT/'case_review_ledger.json').read_text())[i]['osm_id'] for i in range(11))
restrictions={'All fire sites':np.ones(len(f),dtype=bool),'Exclude GNIS-tagged sites':~f.gnis_tag,'Polygons only':f.polygon,'Last edit since 2020':f.last_edit_year>=2020,'Last edit since 2023':f.last_edit_year>=2023,'Exclude all 11 reviewed flags':~f.osm_id.isin(reviewed),'Numbered stations only':f.numbered_station}
sens=[]
for label,keep in restrictions.items():
    for region in regions:
        a=f[keep&f.region.eq(region)]
        rural=a[a.rural];urban=a[a.ur_class.eq('Urban')]
        if len(rural) and len(urban):
            for r in [50,100,200]:sens.append({'restriction':label,'region':region,'radius_m':r,'rural_sites':len(rural),'urban_sites':len(urban),'rural_rate':rural[f'compatible_{r}m'].mean(),'urban_rate':urban[f'compatible_{r}m'].mean(),'urban_minus_rural_pp':100*(urban[f'compatible_{r}m'].mean()-rural[f'compatible_{r}m'].mean())})
pd.DataFrame(sens).to_csv(OUT/'equity_rural_gap_sensitivity.csv',index=False)
# Whole-tract contextual counts; a person is counted once here, never once per station.
communities=[]
for keys,g in t[t.osm_fire_sites>0].groupby(['region','tract_rurality'],dropna=False):
    one=g[g.osm_fire_sites==1];none=g[g.no_local_match_100m]
    communities.append({'region':keys[0],'ur_class':keys[1],'tracts_with_osm_fire':len(g),'mean_tract_correspondence':g.correspondence_100m.mean(),'tracts_no_local_match':len(none),'tracts_no_local_match_share':len(none)/len(g),'population_in_no_match_tracts':int(none.pop_total.sum()),'one_site_tracts':len(one),'one_site_unmatched_tracts':int(one.one_mapped_site_unmatched.sum()),'one_site_unmatched_share':float(one.one_mapped_site_unmatched.mean()) if len(one) else None,'population_in_one_site_unmatched_tracts':int(one.loc[one.one_mapped_site_unmatched,'pop_total'].sum())})
pd.DataFrame(communities).to_csv(OUT/'equity_community_context.csv',index=False)
# Covariate-only tract matching. Dummy columns allow unmatched rural tracts.
eligible=t[(t.osm_fire_sites>0)&t.tract_rurality.isin(['Rural','Urban'])&(t.pop_total>0)&t.svi_overall.notna()&t.wildfire_rank.notna()].copy()
eligible['log_pop']=np.log(eligible.pop_total);pairs=[]
for (region,count),g in eligible.groupby(['region','osm_fire_sites']):
    rr=g[g.tract_rurality.eq('Rural')].sort_values('GEOID');uu=g[g.tract_rurality.eq('Urban')].sort_values('GEOID')
    if not len(rr) or not len(uu):continue
    dx=np.abs(rr.log_pop.to_numpy()[:,None]-uu.log_pop.to_numpy()[None,:]);ds=np.abs(rr.svi_overall.to_numpy()[:,None]-uu.svi_overall.to_numpy()[None,:]);dw=np.abs(rr.wildfire_rank.to_numpy()[:,None]-uu.wildfire_rank.to_numpy()[None,:])
    valid=(dx<=np.log(1.3))&(ds<=.2)&(dw<=.2)
    costs=(dx/np.log(1.3))**2+(ds/.2)**2+(dw/.2)**2
    # Penalty larger than all possible total valid-distance savings gives maximum cardinality.
    penalty=4*(len(rr)+len(uu)+1);mat=np.concatenate([np.where(valid,costs,penalty*3),np.full((len(rr),len(rr)),penalty)],axis=1)
    rid,uid=linear_sum_assignment(mat)
    for i,j in zip(rid,uid):
        if j>=len(uu) or not valid[i,j]:continue
        a=rr.iloc[i];b=uu.iloc[j]
        row={'region':region,'rural_GEOID':a.GEOID,'urban_GEOID':b.GEOID,'rural_county':a.county,'urban_county':b.county,'osm_fire_sites':int(count),'matching_cost':float(costs[i,j])}
        for c in ['pop_total','log_pop','svi_overall','wildfire_rank','usfs_Exposure_mean','polygon_share','gnis_share','mean_record_age','heat_rank','drought_rank','ALAND']:
            row['rural_'+c]=float(a[c]);row['urban_'+c]=float(b[c])
        for r in [50,100,200]:
            row[f'rural_rate_{r}m']=float(a[f'correspondence_{r}m']);row[f'urban_rate_{r}m']=float(b[f'correspondence_{r}m']);row[f'urban_minus_rural_pp_{r}m']=100*(row[f'urban_rate_{r}m']-row[f'rural_rate_{r}m'])
        pairs.append(row)
p=pd.DataFrame(pairs);p.to_csv(OUT/'equity_matched_tract_pairs.csv',index=False)
def cluster_bootstrap(values,clusters,B=4000):
    unique=np.unique(clusters);idx=[np.flatnonzero(clusters==c) for c in unique]
    sums=np.array([values[i].sum() for i in idx]);ns=np.array([len(i) for i in idx]);boot=RNG.integers(0,len(unique),(B,len(unique)))
    estimates=sums[boot].sum(axis=1)/ns[boot].sum(axis=1)
    return [float(v) for v in np.quantile(estimates,[.025,.975])]
balance=[]
for feature in ['log_pop','svi_overall','wildfire_rank','polygon_share','gnis_share','mean_record_age','heat_rank','drought_rank']:
    scale=np.sqrt((eligible.loc[eligible.tract_rurality.eq('Rural'),feature].var()+eligible.loc[eligible.tract_rurality.eq('Urban'),feature].var())/2)
    balance.append({'feature':feature,'before_smd':float((eligible.loc[eligible.tract_rurality.eq('Rural'),feature].mean()-eligible.loc[eligible.tract_rurality.eq('Urban'),feature].mean())/scale),'after_smd':float((p['rural_'+feature].mean()-p['urban_'+feature].mean())/scale),'matched_rural_mean':p['rural_'+feature].mean(),'matched_urban_mean':p['urban_'+feature].mean()})
pd.DataFrame(balance).to_csv(OUT/'equity_match_balance.csv',index=False)
matched=[]
for region,g in [('All matched regions',p)]+list(p.groupby('region')):
    row={'region':region,'pairs':len(g),'rural_counties':g.rural_county.nunique(),'urban_counties':g.urban_county.nunique()}
    for r in [50,100,200]:
        row[f'rural_rate_{r}m']=g[f'rural_rate_{r}m'].mean();row[f'urban_rate_{r}m']=g[f'urban_rate_{r}m'].mean();row[f'urban_minus_rural_pp_{r}m']=g[f'urban_minus_rural_pp_{r}m'].mean()
    row['county_bootstrap_95_interval_pp']=cluster_bootstrap(g.urban_minus_rural_pp_100m.to_numpy(),g.rural_county.to_numpy()) if g.rural_county.nunique()>1 else None
    matched.append(row)
# Supplemental linear probability models: estimates are adjusted associations, not causal effects.
models=[]
def fit_model(label,feature_cols):
    a=f[f.ur_class.isin(['Rural','Urban'])].copy();a['log_pop']=np.log1p(a.pop_total);a['log_supply']=np.log1p(a.osm_fire_sites);a['log_density']=np.log1p(a.pop_total/(a.ALAND/1e6))
    a=a.dropna(subset=feature_cols+['compatible_100m']);columns=[np.ones(len(a))];names=['Intercept']
    for name in feature_cols:
        x=a[name].astype(float).to_numpy();columns.append(x);names.append(name)
    for region in regions[1:]:columns.append(a.region.eq(region).astype(float).to_numpy());names.append('region_'+region)
    X=np.array(columns).T;y=a.compatible_100m.astype(float).to_numpy();bread=np.linalg.pinv(X.T@X);beta=bread@X.T@y;res=y-X@beta
    clusters=a.county.to_numpy();score=np.vstack([(X[clusters==c]*res[clusters==c,None]).sum(axis=0) for c in np.unique(clusters)]);G=len(score);N,K=X.shape
    cov=bread@(score.T@score)@bread*(G/(G-1))*((N-1)/(N-K));se=np.sqrt(np.maximum(0,np.diag(cov)));q=student_t.ppf(.975,G-1)
    for i,name in enumerate(names):
        if name in ['rural','svi_overall','wildfire_rank','log_density','gnis_tag','polygon','record_age_years']:models.append({'model':label,'term':name,'coefficient_pp':float(beta[i]*100),'ci_low_pp':float((beta[i]-q*se[i])*100),'ci_high_pp':float((beta[i]+q*se[i])*100),'sites':N,'counties':G,'rank':int(np.linalg.matrix_rank(X)),'columns':K})
fit_model('Region only',['rural'])
needs=['rural','log_pop','log_supply','svi_overall','wildfire_rank','heat_rank','drought_rank']
fit_model('Region + community need/supply',needs)
fit_model('Region + need/supply + map-record features',needs+['polygon','gnis_tag','record_age_years','named','numbered_station'])
fit_model('Density sensitivity',needs+['polygon','gnis_tag','record_age_years','named','numbered_station','log_density'])
pd.DataFrame(models).to_csv(OUT/'equity_adjusted_associations.csv',index=False)
# Useful cases selected by pre-existing adjudication, not by searching for high-vulnerability errors.
review=json.loads((OUT/'case_review_ledger.json').read_text());case_context=[]
for c in review:
    a=t[t.GEOID==c['origin_tract']].iloc[0]
    case_context.append({'name':c['name'],'verdict':c['verdict'],'GEOID':a.GEOID,'region':a.region,'rurality':a.tract_rurality,'population':int(a.pop_total),'svi':float(a.svi_overall) if pd.notna(a.svi_overall) else None,'svi_band':str(a.svi_band),'high_wildfire':str(a.high_wildfire),'wildfire_rank':float(a.wildfire_rank),'tribal_area_fraction':float(a.tribal_pct),'tribal_legal_fraction':float(a.tribal_legal_pct),'tribal_statistical_fraction':float(a.tribal_stat_pct),'tribal_area_name':str(a.aiannh_name),'tribal_area_kind':str(a.aiannh_kind),'osm_fire_sites':int(a.osm_fire_sites),'matched_100m':int(a.matched_100m)})
(OUT/'equity_named_case_context.json').write_text(json.dumps(case_context,indent=2))
f.to_csv(OUT/'equity_fire_site_analysis.csv',index=False)
t.drop(columns=['geometry','bbox'],errors='ignore').to_csv(OUT/'equity_tract_analysis.csv',index=False)
summary={'fire_sites':len(f),'classified_rural_urban_sites':int(f.ur_class.isin(['Rural','Urban']).sum()),'tracts_with_osm_fire':int((t.osm_fire_sites>0).sum()),'all_supplied_tracts':len(t),'counties_with_sites':f.county.nunique(),'svi_missing_sites':int(f.svi_overall.isna().sum()),'matching_eligible_rural_tracts':int(eligible.tract_rurality.eq('Rural').sum()),'matching_eligible_urban_tracts':int(eligible.tract_rurality.eq('Urban').sum()),'matched_results':matched,'matching_balance':balance,'svi_rank_universes':sorted(s.svi_rank_universe.dropna().unique()),'protocol':protocol,'random_seed':20261024}
(OUT/'equity_analysis_results.json').write_text(json.dumps(summary,indent=2))
print('MATCHED',json.dumps(matched,indent=2),flush=True)
print('MODELS',pd.DataFrame(models).query("term == 'rural'").to_string(index=False),flush=True)
print('POOLED',pd.DataFrame(pooled)[['analysis','ur_class','svi_band','high_wildfire','tribal_band','sites','rate_100m']].to_string(index=False),flush=True)
print('COMMUNITIES',pd.DataFrame(communities).to_string(index=False),flush=True)
print('BALANCE',pd.DataFrame(balance).to_string(index=False),flush=True)
print('CASES',json.dumps(case_context,indent=2),flush=True)
