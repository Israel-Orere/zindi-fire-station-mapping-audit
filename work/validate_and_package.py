from run_discovery import *
import shutil,zipfile,platform
checks={};allrows=[];manifest=[]
for region in REGIONS:
    path=OUT/f'{region}_facility_audit.csv'
    if not path.exists():continue
    d=pd.read_csv(path,dtype={'GEOID':str});allrows.append(d)
    raw=json.loads((CACHE/f'{region}.json').read_text(encoding='utf-8'))
    samples=set(pd.read_csv(DATA/f'{region}-sample-submission.csv',dtype={'GEOID':str}).GEOID)
    c={'rows':len(d),'unique_osm_ids':d.osm_id.is_unique,'valid_geoids':bool(d.GEOID.str.fullmatch(r'\d{11}').all()),'all_in_supplied_samples':set(d.GEOID)<=samples,'historical_timestamps_valid':all(e.get('timestamp','')<=DATE for e in raw['elements']),'radius_monotonicity':bool(((~d.compatible_50m|d.compatible_100m)&(~d.compatible_100m|d.compatible_200m)).all()),'group_count_reconciles':int(d.groupby(['ur_class','facility_type'],dropna=False).size().sum())==len(d)}
    assert all(c[k] for k in c if k!='rows'),(region,c)
    checks[region]=c
    for suffix,folder in [('overture-pois.parquet','reference'),('census-tracts.parquet','strata'),('strata-tract-table.csv','strata'),('sample-submission.csv','reference')]:
        p=DATA/f'{region}-{suffix}'
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        manifest.append({'name':p.name,'bytes':p.stat().st_size,'sha256':h,'url':f'https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/{folder}/{region}/{p.name}'})
physical=json.loads((OUT/'physical_site_checks.json').read_text());assert physical['porum']['intersecting_overture_buildings']>=1 and physical['porum']['point_inside_overture_building']
case=json.loads((OUT/'named_case_evidence.json').read_text())['porum'];assert 44000<case['point_distance_m']<45000 and case['overture']['mapped_GEOID']=='40101000400'
checkall={'regional_checks':checks,'porum_building_overlap':True,'porum_coordinate_discrepancy_44_45km':True,'package_regions':list(checks),'python':platform.python_version(),'interpretation':'Checks validate computational integrity, not OSM operational status or causal effects.'}
namepairs=pd.read_csv(OUT/'exact_name_location_audit.csv',dtype={'GEOID':str,'destination_GEOID':str})
checkall['exact_name_review']={'pairs':len(namepairs),'over_500m_candidates':int((namepairs.distance_m>500).sum()),'over_500m_same_tract_candidates':int(((namepairs.distance_m>500)&namepairs.same_tract).sum()),'interpretation':'Unique-name coordinate differences are review candidates; station/department or headquarters distinctions can explain some.'}
cases=json.loads((OUT/'case_review_ledger.json').read_text())
assert len(cases)==11 and len({c['osm_id'] for c in cases})==11
assert set(c['osm_id'] for c in cases)==set(namepairs.loc[namepairs.distance_m>500,'osm_id'])
assert collections.Counter(c['verdict'] for c in cases)=={'supported_location_error':3,'distinct_facilities':5,'unresolved':3}
assert all(c['sources'] and c['finding'] and c['interpretation'] and c['next_check'] for c in cases)
assert all(not c['compatible_fire_place_within_200m'] for c in cases if c['verdict']=='supported_location_error')
assert all(c['physical_checks']['osm']['point_inside_building'] for c in cases if c['verdict']=='supported_location_error')
assert next(c for c in cases if c['key']=='westport')['county_address_point_distance_to_osm_m']<1
assert all(next(c for c in cases if c['key']==key)['compatible_fire_place_within_200m'] for key in ['redding','foresthill','mesa'])
combined=pd.read_csv(OUT/'facility_audit.csv',dtype={'GEOID':str});assert len(combined)==sum(len(d) for d in allrows)
assert (combined.facility_type=='fire').sum()==1372
from html.parser import HTMLParser
class ReportParser(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.images=[];self.case_ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='img':self.images.append(a.get('src',''))
        if tag=='article' and 'case ' in a.get('class',''):self.case_ids.append(a.get('id'))
reports={}
for filename in ['bias_discovery_visual_report.html','comprehensive_case_audit.html']:
    parser=ReportParser();parser.feed((OUT/filename).read_text(encoding='utf-8'))
    for href in parser.links:
        if not href.startswith(('http:','https:','#','mailto:')):assert (OUT/href.split('#')[0]).exists(),(filename,href)
    assert all(src.startswith('data:image/png;base64,') for src in parser.images)
    reports[filename]={'embedded_figures':len(parser.images),'local_links_resolve':True,'case_cards':len(parser.case_ids)}
assert reports['comprehensive_case_audit.html']['case_cards']==11
assert reports['comprehensive_case_audit.html']['embedded_figures']==11
assert reports['bias_discovery_visual_report.html']['embedded_figures']==4
story_chart=pd.read_csv(OUT/'rural_urban_story_chart_data.csv')
published_rates=pd.read_csv(OUT/'retention_by_region.csv')
assert len(story_chart)==8
for row in story_chart.itertuples():
    reference=published_rates[(published_rates.region==row.region)&(published_rates.ur_class==row.group)&(published_rates.facility_type=='fire')].iloc[0]
    assert row.sites==reference.sites
    assert row.nearby_listings==round(reference.sites*reference.compatible_100m)
    assert abs(row.percent-100*reference.compatible_100m)<1e-8
checkall['story_chart']={'regional_groups':8,'agrees_with_existing_regional_results':True,'denominator':'All Rural/Urban fire sites; not one-site tracts','unknown_rurality_excluded':1}
exposure_groups=pd.read_csv(OUT/'wildfire_story_exposure_groups.csv')
exposure_summary=json.loads((OUT/'wildfire_story_summary.json').read_text())
assert len(exposure_groups)==12 and exposure_groups.sites.sum()==1372
for region,g in exposure_groups.groupby('region'):
    reference=combined[(combined.region==region)&(combined.facility_type=='fire')]
    assert g.sites.sum()==len(reference) and g.matched.sum()==reference.compatible_100m.sum()
assert exposure_groups.loc[exposure_groups.exposure_group=='Lowest exposure quarter','rural_sites'].sum()==0
assert (exposure_groups.rural_sites+exposure_groups.urban_sites+exposure_groups.unknown_rurality_sites==exposure_groups.sites).all()
assert abs(exposure_summary['wildfire_25th_to_75th_rank_adjusted_gap_pp']-14.426595322122019)<1e-8
checkall['wildfire_story']={'groups':12,'all_sites_reconcile':True,'rural_urban_composition_disclosed':True,'uses_existing_adjusted_estimate':True,'chart':'Observed shares, not adjusted predictions','added_descriptively':'2026-10-27'}
checkall['case_adjudication']={'reviewed':11,'supported_location_errors':3,'distinct_facilities':5,'unresolved':3,'all_over_500m_candidates_reviewed':True,'supported_sites_buildings_retained':True,'local_record_false_alarms_verified':True,'westport_county_address_within_one_metre':True}
checkall['combined_fire_sites']=1372;checkall['reports']=reports
checkall['interactive_browser_check']='Blocked: local file protocol is not permitted by browser security policy. Saved HTML structure, image embeds, local links, map images and calculations were checked directly. No browser workaround attempted.'
(OUT/'validation.json').write_text(json.dumps(checkall,indent=2))
(OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
codefiles=['run_discovery.py','analyze_discovery.py','audit_name_displacements.py','fetch_map_layers.py','render_figures.py','build_story_overview.py','build_wildfire_story.py','build_report.py','export_case_evidence.py','build_case_audit.py','extract_full_case_context.py','check_recurrence_candidates.py','fetch_all_ten_maps.py','fetch_mesa_case_maps.py','fetch_case_histories.py','retry_regions_tiled.py','retry_texas_subtiles.py','resolve_address_cases.py','validate_and_package.py']
if (OUT/'equity_validation.json').exists():
    codefiles+=['analyze_equity.py','equity_followup_checks.py','build_equity_report.py','validate_equity.py']
    checkall['equity_followup']=json.loads((OUT/'equity_validation.json').read_text())
    (OUT/'validation.json').write_text(json.dumps(checkall,indent=2))
# User-facing archive contains portable code, raw OSM responses, compact Overture map windows,
# derived outputs and hashes. Large original POIs stay at their public source URLs.
bundle=OUT/'zindi_bias_discovery_evidence.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
    for name in codefiles:
        source=(ROOT/'work'/name).read_text(encoding='utf-8')
        source='\n'.join(line for line in source.splitlines() if not (line.startswith('OLD=') or line.startswith('sys.path[:0]')))+'\n'
        source=re.sub(r"DATA=Path\(os\.environ\.get\('ZINDI_DATA_DIR',r'.*?'\)\)","DATA=Path(os.environ.get('ZINDI_DATA_DIR',str(ROOT/'data')))",source)
        z.writestr('work/'+name,source)
    for f in CACHE.iterdir():
        if f.suffix in ['.json','.geojson','.overpassql']:z.write(f,'work/osm/'+f.name)
    for name in ['map_windows.json','eastern-ok_buildings_map.geojson','eastern-ok_roads_map.geojson','tract_analysis.csv','case_decisions.json','original_ten_cases.json','recurrence_candidates.json','full_case_context.json','equity_analysis_protocol.json','equity_followup_protocol.json','equity_strict_pairs_0.1.csv','equity_strict_pairs_0.05.csv','story_writeup.md','story_analysis_notes.md','reproduce_analysis.md']+[p.name for p in (ROOT/'work').glob('*_all_ten_*_map.geojson')]+[p.name for p in (ROOT/'work').glob('*_mesa_*_map.geojson')]:
        p=ROOT/'work'/name
        if p.exists():z.write(p,'work/'+name)
    for f in (ROOT/'work/osm_history').glob('*.json'):z.write(f,'work/osm_history/'+f.name)
    for name in ['westport_official_address_query.json','visual_source_observations.json','washington_plan_relevant_excerpt.txt','manifest.json','additional_manifest.json']:
        p=ROOT/'work/review_sources'/name
        if p.exists():z.write(p,'work/review_sources/'+name)
    for name in ['mendocino_address_item.json','mendocino_address_layer.json']:
        p=ROOT/'work/public_gis'/name
        if p.exists():z.write(p,'work/public_gis/'+name)
    for f in OUT.iterdir():
        if f.is_file() and f.suffix in ['.md','.html','.png','.svg','.csv','.json']:z.write(f,'outputs/'+f.name)
    z.writestr('requirements.txt','numpy\npandas\npyarrow\nshapely\nmatplotlib\nscipy\nscikit-learn\n')
    z.writestr('download_inputs.py',"from pathlib import Path\nimport json,urllib.request,hashlib\nr=Path(__file__).resolve().parent\nd=r/'data';d.mkdir(exist_ok=True)\nfor item in json.loads((r/'outputs/input_manifest.json').read_text()):\n p=d/item['name']\n if not p.exists():\n  print('Downloading',item['name'],flush=True)\n  urllib.request.urlretrieve(item['url'],p)\n assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],('Input changed',p)\n")
    z.writestr('README.md','''# Zindi Best Bias Discovery evidence

Read outputs/comprehensive_case_audit.html for all 11 decisions, sources and equal-scale endpoint maps. The short narrative is outputs/bias_discovery_visual_report.html. Method, caveats, attribution and licensing are in outputs/methodology.md. Both HTML files embed their figures and work offline. Source links require internet.

The article links this package near the top. Once extracted, the code is already in work/; read outputs/reproduce_analysis.md for a single ordered run sequence and source-file guide. The original large challenge inputs are downloaded separately with download_inputs.py and verified against the manifest.

The article leads with the actual discoveries. Its short interpretation note links outputs/article_analysis_notes.md, which retains the full qualifications, rural adjustment results, exposure-group composition, model uncertainty, case-verification limits and hypothetical-consequence boundaries. work/story_analysis_notes.md is the authored source for that companion; build_report.py exports it with the main article.

The short report now starts with a direct regional rural/urban chart. Run python work/build_story_overview.py before python work/build_report.py to redraw it. Its exact counts are in outputs/rural_urban_story_chart_data.csv; PNG and SVG versions are included. This is the all-sites comparison, not the separate one-station-tract analysis.

The wildfire deep dive adds a descriptive chart of all three exposure groups in every region. Run python work/build_wildfire_story.py after the equity analysis and before build_report.py. It uses existing exposure ranks and model outputs, fits no new model, and exports all 12 groups plus their rural/urban composition. The raw chart groups differ from the existing adjusted 25th-to-75th-percentile model contrast. Every lowest-quarter site is urban in this sample, an important limitation made explicit in the article.

Read outputs/equity_followup_report.html for the closer equity analysis. It reports the wildfire association, weakened independent rural association, vulnerability/tribal nulls and reversals, tract-level context, matching overlap and every subgroup denominator. Its three figures are embedded. Protocols distinguish the initial equity plan from exploratory sensitivity checks. No causal effect, operating-station census or number of people harmed is established.

To recompute offline after downloading inputs: install requirements.txt, run python download_inputs.py (public challenge inputs; several hundred MB), then run python work/run_discovery.py eastern-ok eastern-wa maricopa-az northern-ca. Do not request Texas: its historical extraction is incomplete and partial data must not be treated as complete. Next run python work/analyze_discovery.py, python work/audit_name_displacements.py, python work/render_figures.py, python work/build_case_audit.py, python work/build_report.py and python work/validate_and_package.py. Run from the extracted project root. Alternatively set ZINDI_DATA_DIR to an existing copy of the manifest-listed inputs. Original OSM responses, case contexts and saved map windows are archived; no live OSM or map-layer request is necessary for audited regions. Case decisions are manual evidence judgments in work/case_decisions.json; the script reproduces their presentation, not their independent verification.

The public-source register retains URLs, access methods and hashes. Full third-party HTML pages and the 71-page vendor contract are not redistributed. Porum contract pages 1–2 were visually checked and the relevant address is documented. Westport uses one county working address record; its source warning is preserved. Some official pages blocked direct retrieval; those claims use indexed official text or city-authored publications, explicitly identified in the case ledger. Recheck live sources before publication because pages can change.

To reproduce the equity follow-up after the base analysis, run python work/analyze_equity.py, python work/equity_followup_checks.py, python work/build_equity_report.py, python work/validate_equity.py, python work/build_report.py and python work/validate_and_package.py. scipy supplies deterministic assignment and distribution functions; scikit-learn provides an independent OLS validation. Random seed: 20261024. The calculations use supplied strata and the archived comparison sites, without extra reference targets or paid services.

This package is discovery evidence only. It contains no new leaderboard prediction and does not use removed reference layers. OSM is an incomplete, potentially stale comparator; discrepancies are not all confirmed real-world omissions. No submission or external publication has been performed.
''')
print(json.dumps({'validation':checkall,'evidence_zip_bytes':bundle.stat().st_size},indent=2),flush=True)
