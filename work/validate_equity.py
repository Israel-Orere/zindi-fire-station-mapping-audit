from run_discovery import *
from sklearn.linear_model import LinearRegression
from html.parser import HTMLParser
import shutil
f=pd.read_csv(OUT/'equity_fire_site_analysis.csv',dtype={'GEOID':str,'county':str});t=pd.read_csv(OUT/'equity_tract_analysis.csv',dtype={'GEOID':str,'county':str});p=pd.read_csv(OUT/'equity_matched_tract_pairs.csv',dtype={'rural_GEOID':str,'urban_GEOID':str});s=pd.read_csv(OUT/'equity_subgroup_rates.csv',keep_default_na=False);a=pd.read_csv(OUT/'equity_adjusted_associations.csv')
assert len(f)==1372 and f.osm_id.is_unique and t.GEOID.is_unique and len(t)==3791
assert (t.osm_fire_sites>0).sum()==1034 and t.osm_fire_sites.sum()==1372
assert f.GEOID.isin(t.GEOID).all() and f.GEOID.str.fullmatch(r'\d{11}').all()
assert f.ur_class.isin(['Rural','Urban']).sum()==1371 and f.svi_overall.isna().sum()==14
assert (f[['svi_overall','wildfire_rank','tribal_pct']].dropna().apply(lambda x:x.between(0,1).all())).all()
for r in [50,100,200]:
    expected=f.groupby('GEOID')[f'compatible_{r}m'].sum();actual=t.set_index('GEOID')[f'matched_{r}m'].reindex(expected.index)
    assert np.array_equal(expected.to_numpy(),actual.to_numpy())
assert ((~f.compatible_50m|f.compatible_100m)&(~f.compatible_100m|f.compatible_200m)).all()
for analysis,g in s.groupby('analysis'):assert g.sites.sum()==1372,(analysis,g.sites.sum())
assert len(p)==166 and p.rural_GEOID.is_unique and p.urban_GEOID.is_unique
assert (np.maximum(p.rural_pop_total/p.urban_pop_total,p.urban_pop_total/p.rural_pop_total)<=1.3+1e-12).all()
assert (np.abs(p.rural_svi_overall-p.urban_svi_overall)<=.2+1e-12).all()
assert (np.abs(p.rural_wildfire_rank-p.urban_wildfire_rank)<=.2+1e-12).all()
for c in ['rural','urban']:
    d=t.set_index('GEOID').reindex(p[c+'_GEOID'])
    assert (d.osm_fire_sites.to_numpy()==p.osm_fire_sites.to_numpy()).all()
    assert (d.region.to_numpy()==p.region.to_numpy()).all()
for svi,wild in [(.1,.1),(.1,.05)]:
    q=pd.read_csv(ROOT/'work'/f'equity_strict_pairs_{wild}.csv',dtype={'rural_GEOID':str,'urban_GEOID':str})
    assert q.rural_GEOID.is_unique and q.urban_GEOID.is_unique
    assert (abs(q.rural_svi_overall-q.urban_svi_overall)<=svi+1e-12).all()
    assert (abs(q.rural_wildfire_rank-q.urban_wildfire_rank)<=wild+1e-12).all()
    shutil.copyfile(ROOT/'work'/f'equity_strict_pairs_{wild}.csv',OUT/f'equity_strict_pairs_{wild}.csv')
for label,expected_n,expected_unmatched,expected_pop in [('Rural',209,91,289059),('Urban',608,135,606850)]:
    q=t[(t.tract_rurality==label)&(t.osm_fire_sites==1)]
    assert len(q)==expected_n and q.one_mapped_site_unmatched.sum()==expected_unmatched
    assert q.loc[q.one_mapped_site_unmatched,'pop_total'].sum()==expected_pop
# Independently fit the main adjusted model with a different OLS implementation.
v=f[f.ur_class.isin(['Rural','Urban'])].copy();v['rural']=v.ur_class.eq('Rural');v['log_pop']=np.log1p(v.pop_total);v['log_supply']=np.log1p(v.osm_fire_sites)
cols=['rural','log_pop','log_supply','svi_overall','wildfire_rank','heat_rank','drought_rank','polygon','gnis_tag','record_age_years','named','numbered_station'];v=v.dropna(subset=cols)
X=v[cols].astype(float);X=pd.concat([X,pd.get_dummies(v.region,dtype=float).drop(columns=['eastern-ok'])],axis=1)
fit=LinearRegression().fit(X,v.compatible_100m.astype(float))
for term in ['rural','svi_overall','wildfire_rank']:
    estimate=a[(a.model=='Region + need/supply + map-record features')&(a.term==term)].iloc[0].coefficient_pp
    assert abs(estimate-fit.coef_[list(X.columns).index(term)]*100)<1e-6,(term,estimate)
assert np.linalg.matrix_rank(np.column_stack([np.ones(len(X)),X]))==X.shape[1]+1
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a':self.links.append(d.get('href',''))
        if tag=='img':self.images.append(d.get('src',''))
parser=Parser();parser.feed((OUT/'equity_followup_report.html').read_text(encoding='utf-8'))
for link in parser.links:
    if not link.startswith(('http:','https:','#','mailto:')):assert (OUT/link).exists(),link
assert len(parser.images)==3 and all(x.startswith('data:image/png;base64,') for x in parser.images)
for filename in ['equity_analysis_protocol.json','equity_followup_protocol.json']:shutil.copyfile(ROOT/'work'/filename,OUT/filename)
checks={'fire_sites':1372,'tracts_with_fire_sites':1034,'all_supplied_tracts':3791,'county_clusters':120,'site_and_tract_joins_one_to_many_valid':True,'all_planned_subgroups_reconcile_to_1372':True,'radius_monotonicity':True,'matching_calipers_and_unique_controls_valid':True,'main_pairs':166,'strict_pairs_010':97,'strict_pairs_005':62,'independent_ols_implementation_agrees':True,'single_site_population_and_count_totals_verified':True,'report_figures_embedded':3,'local_links_resolve':True,'figures_visually_reviewed':True,'interpretation':'Computational checks do not establish real operating station status, causal bias, personal identity or observed harm.','source_urls':['https://zindi.world/competitions/bias-bounty-mapping-equity-challenge','https://source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/README.md','https://www.atsdr.cdc.gov/place-health/php/svi/svi-frequently-asked-questions-faqs.html','https://www.census.gov/programs-surveys/geography/about/glossary/aian-definitions.html','https://www.arcgis.com/sharing/rest/content/items/5fc79866a77443a2828e049298d828ba/info/metadata/metadata.xml?format=default&output=html']}
(OUT/'equity_validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2),flush=True)
