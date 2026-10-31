from run_discovery import *
from scipy.optimize import linear_sum_assignment
from scipy.stats import t as student_t
f=pd.read_csv(OUT/'equity_fire_site_analysis.csv',dtype={'GEOID':str,'county':str},keep_default_na=False)
t=pd.read_csv(OUT/'equity_tract_analysis.csv',dtype={'GEOID':str,'county':str})
regions=[r for r in REGIONS if r in set(f.region)]
# These follow-ups were specified after the first equity tables and are exploratory.
followup_protocol={'strict_match_variants':[{'svi_caliper':.1,'wildfire_rank_caliper':.1},{'svi_caliper':.1,'wildfire_rank_caliper':.05}],'purpose':'Assess residual imbalance in the initial matched cohort; do not select a preferred result based on its outcome.','exploratory_hazard_sensitivity':['Burn probability percentile instead of Exposure Type percentile','Exposure Type by separate region','Exposure Type after removing GNIS records and after restricting polygons','Exposure Type with and without density adjustment'],'warning':'Exposure Type is a landscape average, not burn probability, housing-weighted personal exposure, station-site hazard or current fire danger. Density and exposure overlap conceptually with rurality.'}
(ROOT/'work/equity_followup_protocol.json').write_text(json.dumps(followup_protocol,indent=2))
rows=[];balances=[];eligible=t[(t.osm_fire_sites>0)&t.tract_rurality.isin(['Rural','Urban'])&(t.pop_total>0)&t.svi_overall.notna()&t.wildfire_rank.notna()].copy();eligible['log_pop']=np.log(eligible.pop_total)
for svi_cal,wild_cal in [(.1,.1),(.1,.05)]:
    pairs=[]
    for (region,count),g in eligible.groupby(['region','osm_fire_sites']):
        rr=g[g.tract_rurality.eq('Rural')].sort_values('GEOID');uu=g[g.tract_rurality.eq('Urban')].sort_values('GEOID')
        if not len(rr) or not len(uu):continue
        dx=np.abs(rr.log_pop.to_numpy()[:,None]-uu.log_pop.to_numpy()[None,:]);ds=np.abs(rr.svi_overall.to_numpy()[:,None]-uu.svi_overall.to_numpy()[None,:]);dw=np.abs(rr.wildfire_rank.to_numpy()[:,None]-uu.wildfire_rank.to_numpy()[None,:]);valid=(dx<=np.log(1.3))&(ds<=svi_cal)&(dw<=wild_cal)
        cost=(dx/np.log(1.3))**2+(ds/svi_cal)**2+(dw/wild_cal)**2;penalty=4*(len(rr)+len(uu)+1)
        ii,jj=linear_sum_assignment(np.concatenate([np.where(valid,cost,penalty*3),np.full((len(rr),len(rr)),penalty)],axis=1))
        for i,j in zip(ii,jj):
            if j>=len(uu) or not valid[i,j]:continue
            a=rr.iloc[i];b=uu.iloc[j];pairs.append({'variant':f'SVI {svi_cal}, wildfire {wild_cal}','region':region,'rural_GEOID':a.GEOID,'urban_GEOID':b.GEOID,'rural_county':a.county,'rural_rate':a.correspondence_100m,'urban_rate':b.correspondence_100m,**{f'{label}_{field}':r[field] for label,r in [('rural',a),('urban',b)] for field in ['log_pop','svi_overall','wildfire_rank','mean_record_age','polygon_share']}})
    p=pd.DataFrame(pairs);p.to_csv(ROOT/'work'/f'equity_strict_pairs_{wild_cal}.csv',index=False)
    for region,g in [('All matched regions',p)]+list(p.groupby('region')):rows.append({'variant':f'SVI {svi_cal}, wildfire {wild_cal}','region':region,'pairs':len(g),'rural_rate':g.rural_rate.mean(),'urban_rate':g.urban_rate.mean(),'urban_minus_rural_pp':100*(g.urban_rate-g.rural_rate).mean()})
    for field in ['log_pop','svi_overall','wildfire_rank','mean_record_age','polygon_share']:
        scale=np.sqrt((eligible.loc[eligible.tract_rurality.eq('Rural'),field].var()+eligible.loc[eligible.tract_rurality.eq('Urban'),field].var())/2)
        balances.append({'variant':f'SVI {svi_cal}, wildfire {wild_cal}','feature':field,'after_smd':(p['rural_'+field].mean()-p['urban_'+field].mean())/scale})
pd.DataFrame(rows).to_csv(OUT/'equity_strict_match_sensitivity.csv',index=False);pd.DataFrame(balances).to_csv(OUT/'equity_strict_match_balance.csv',index=False)
for region in regions:
    idx=t.region.eq(region);t.loc[idx,'bp_rank']=t.loc[idx,'usfs_BP_mean'].rank(pct=True)
f['bp_rank']=f.GEOID.map(t.set_index('GEOID').bp_rank)
models=[]
def model(data,label,hazard='wildfire_rank',density=False,radius=100):
    a=data[data.ur_class.isin(['Rural','Urban'])].copy();a['rural']=a.ur_class.eq('Rural');a['log_pop']=np.log1p(a.pop_total);a['log_supply']=np.log1p(a.osm_fire_sites);a['log_density']=np.log1p(a.pop_total/(a.ALAND/1e6));a['svi_overall']=pd.to_numeric(a.svi_overall,errors='coerce')
    cols=['rural','log_pop','log_supply','svi_overall',hazard,'heat_rank','drought_rank','polygon','gnis_tag','record_age_years','named','numbered_station']+(['log_density'] if density else [])
    a=a.dropna(subset=cols);cols=[c for c in cols if a[c].nunique()>1];parts=[np.ones(len(a))]+[a[c].astype(float).to_numpy() for c in cols];names=['intercept']+cols
    present=[r for r in regions if r in set(a.region)]
    for r in present[1:]:parts.append(a.region.eq(r).astype(float).to_numpy());names.append(r)
    X=np.array(parts).T;y=a[f'compatible_{radius}m'].astype(float).to_numpy();bread=np.linalg.pinv(X.T@X);beta=bread@X.T@y;res=y-X@beta;clusters=a.county.to_numpy();score=np.vstack([(X[clusters==c]*res[clusters==c,None]).sum(axis=0) for c in np.unique(clusters)]);G=len(score);N,K=X.shape
    assert np.linalg.matrix_rank(X)==K,(label,'rank deficiency')
    cov=bread@(score.T@score)@bread*(G/(G-1))*((N-1)/(N-K));j=names.index(hazard);se=np.sqrt(cov[j,j]);q=student_t.ppf(.975,G-1)
    models.append({'model':label,'hazard':hazard,'sites':N,'counties':G,'association_per_rank_iqr_pp':float(beta[j]*50),'ci_low_pp':float((beta[j]-q*se)*50),'ci_high_pp':float((beta[j]+q*se)*50)})
model(f,'Exposure Type, all regions')
model(f,'Exposure Type + density',density=True)
model(f[~f.gnis_tag],'Exposure Type, exclude GNIS')
model(f[f.polygon],'Exposure Type, polygons only')
model(f,'Burn probability, all regions',hazard='bp_rank')
model(f,'Exposure Type, 50 m threshold',radius=50)
model(f,'Exposure Type, 200 m threshold',radius=200)
for region in regions:model(f[f.region.eq(region)],'Exposure Type, '+region)
pd.DataFrame(models).to_csv(OUT/'equity_wildfire_association_sensitivity.csv',index=False)
print('STRICT MATCHING',pd.DataFrame(rows).to_string(index=False),flush=True);print('BALANCE',pd.DataFrame(balances).to_string(index=False),flush=True);print('HAZARD',pd.DataFrame(models).to_string(index=False),flush=True)
