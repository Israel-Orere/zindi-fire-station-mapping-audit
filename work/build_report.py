from run_discovery import *
import html,shutil,zipfile,os
d=pd.concat([pd.read_csv(OUT/f'{r}_facility_audit.csv',dtype={'GEOID':str}) for r in REGIONS if (OUT/f'{r}_facility_audit.csv').exists()],ignore_index=True)
f=d[d.facility_type=='fire'];regions=[r for r in REGIONS if r in set(f.region)]
names={'eastern-ok':'Eastern Oklahoma','eastern-wa':'Eastern Washington*','maricopa-az':'Maricopa + surrounding','northern-ca':'Northern California','south-central-tx':'South-Central Texas'}
tab=[];recurs=0
for region in regions:
    rr=f[(f.region==region)&(f.ur_class=='Rural')];uu=f[(f.region==region)&(f.ur_class=='Urban')]
    if len(rr) and len(uu):
        rp=rr.compatible_100m.mean();up=uu.compatible_100m.mean();recurs+=rp<up
        tab.append(f'| {names[region]} | {int(rr.compatible_100m.sum())}/{len(rr)} ({rp:.1%}) | {int(uu.compatible_100m.sum())}/{len(uu)} ({up:.1%}) | {(up-rp)*100:.1f} pp |')
source='https://source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge'
county='https://muskogee.okcounties.org/offices/fire-departments'
contract='https://muskogee.okcounties.org/file/item_8_-_contract_porum_vfd_fire_master_fire_equipment_2427.pdf'
event='https://oklahoma.gov/oem/emergencies-and-disasters/2007/01-12-winter-weather/situation-update-9.html'
rules='https://zindi.world/competitions/bias-bounty-mapping-equity-challenge'
# The narrative is reviewed prose; evidence calculations remain in their analysis scripts.
article=(ROOT/'work/story_writeup.md').read_text(encoding='utf-8')
article_title=article.splitlines()[0].removeprefix('# ')
(OUT/'bias_discovery_writeup.md').write_text(article,encoding='utf-8')
(OUT/'article_analysis_notes.md').write_text((ROOT/'work/story_analysis_notes.md').read_text(encoding='utf-8'),encoding='utf-8')
(OUT/'reproduce_analysis.md').write_text((ROOT/'work/reproduce_analysis.md').read_text(encoding='utf-8'),encoding='utf-8')
method='''# Method and reproducibility

This is an exploratory Best Bias Discovery audit, not a reconstruction of organizer targets. No TIGER road reference, standalone Microsoft footprint reference, HIFLD/USGS facility reference, CBP establishment reference or removed coverage-gap file was read. All building/road geometries shown come from currently supplied Overture extracts.

## Inputs and dates

- Challenge inputs: Source Cooperative, Overture 2026-08-19.0, tract boundaries and strata. Direct URLs and SHA-256 hashes are in input_manifest.json.
- Public OSM: historical 2026-08-01T00:00:00Z, retrieved 2026-10-24 through Overpass. Queries, original JSON and retrieval manifests are archived. The response's timestamp_osm_base describes server freshness, not the requested historical date; the query controls that date.
- Other public pages are contextual verification of named examples. No operational directory was converted into reference totals or prediction inputs.

## Facility and match definitions

- Main analysis selects amenity=fire_station on nodes, ways and relations. Oklahoma additionally selects amenity=school for a separate diagnostic. Schools are not sampled in other regions.
- Exclude explicit disused=yes or abandoned=yes. This cannot establish that remaining objects are operational. OSM is not ground truth.
- Convert a closed way to a polygon; relations use the largest available closed outer ring, with bounds-centre fallback if needed. Inner holes and secondary relation parts are not modeled. Representative points assign sites to one supplied tract; some assignment ambiguity is possible at boundaries.
- Deduplicate overlapping same-type geometries when normalized names agree or one is unnamed. Merge same-name same-type sites less than 60 m apart. Separate services or nearby stations may still be merged; some duplicate nodes may remain. Duplicate IDs are retained in osm_duplicates. Multi-station department naming remains a limitation.
- Compatible Overture category: fire_department; school types: elementary_school, middle_school, high_school, school, private_school, public_school. Any primary or alternate category qualifies. primary_100m provides a stricter diagnostic. No Overture confidence cutoff is imposed.
- Correspondence requires a compatible place within 100 m of OSM geometry; 50 and 200 m are sensitivity tests. Proximity/category matching does not certify entity identity. Local equirectangular distances in metres are used; minor projection error is negligible for these thresholds but 44.4 km is approximate.
- A name-assisted diagnostic allows normalized-name similarity >=0.8 with a compatible category within 350 m. The normalization removes punctuation, volunteer, department and school. Similarity is a heuristic. Its rates are not substituted into the primary result.
- A separate exact-name audit requires normalized names unique in the analyzed OSM sites and in the supplied Overture region, excluding generic labels such as Fire Station 1. It records coordinate differences, source and destination tracts, confidence, category and source. Headquarters and station names can still coincide. These are discrepancy candidates, not automatically confirmed errors.
- All 11 exact-name pairs above 500 m in four complete regions were independently reviewed against official sources, both endpoint map windows, nearby places and OSM object history (history for the original ten). The result is three supported location errors, five distinct-facility pairings and three unresolved cases. Three of the distinct-facility pairs already have compatible local Overture records. Two others are branch-coverage leads. See case_review_ledger.json for source access limitations, evidence strength and next checks. Current pages are not automatically evidence of snapshot-time operations.
- The 500 m review threshold is a triage choice. Seven more unique-name pairs lie between 100 and 500 m and are disclosed without classifying them as verified errors. The exact-name screen misses unnamed sites, aliases, duplicate department names and records beyond the region extract. The 1,372-site proximity comparison and the 252-pair identity screen have different denominators and purposes.
- Westport verification used one published department address and one county address point. Mendocino's working-layer metadata explicitly warns of errors and inconsistencies; no countywide address dataset was created. Porum's scanned contract was read visually on pages 1–2; it has no extractable text. Broken Arrow's current directory blocked direct retrieval, so the review also uses the city-authored 2021 annual report and indexed official opening notices.
- Four regions have complete historical extracts: eastern-ok, eastern-wa, maricopa-az and northern-ca. Texas is incomplete after whole-region, tile and subtile requests; it contributes no rates or screened candidates. Washington is supplementary rather than a leaderboard region. Footprint agreement may share upstream OSM data and is evidence of layer retention, not independent operational ground truth.
- Rural/Urban labels are the supplied tract ur_class. Unknown labels are retained in the data and excluded from the rural/urban comparison; denominators are reported explicitly. Counts are site-weighted, not population-weighted.
- Regional rates are descriptive, not matched causal estimates. Sensitivity lines are not confidence intervals. The two illustrated tracts have equal OSM fire-site supply and population within 30%; the urban candidate minimizes log-population difference plus squared standardized wildfire exposure, heat days and summer drought differences. Controls were selected without using match outcomes. Missing hazard values receive a penalty. No full matched-cohort effect is claimed.

## Important negative result

Adair tract 40001377000 was the original lead. The audit finds Bell School, Zion Public School and Peavine School records in Overture. Bell is approximately 128.5 m from its OSM point; a 100 m-only test would call it unmatched although the name and category are retained. Oak Ridge School's unmatched legacy OSM point has not been verified as an operating school. Thus the original Adair 'empty community' narrative is unsupported and was not used.

## Validation

Historical object timestamps, unique OSM IDs after deduplication, matched radius monotonicity, 11-character GEOIDs, count reconciliation, both illustrated sites' footprint/road relationships and named-record source/destination locations are checked in validation.json. The archival raw inputs allow recomputing results without relying on a live Overpass server. Current Overpass may return later corrected history; compare checksums.

## Licensing and attribution

- © OpenStreetMap contributors, ODbL 1.0: https://www.openstreetmap.org/copyright . Derived comparison tables and OSM extracts are distributed under ODbL with source attribution. Underlying OSM usernames/IDs of contributors are omitted from the presentation but original public raw metadata is retained for reproducibility.
- Overture Places: provider licenses, including Meta CDLA-Permissive-2.0, are retained in named_case_evidence.json. Overture buildings/transportation have their applicable attribution and licenses; see https://docs.overturemaps.org/attribution/ . These maps include OSM-derived Overture geometry.
- Challenge package: https://source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge ; Zindi lists CC-BY-SA 4.0. Preserve upstream source licenses when reusing extracts.
- Analysis code: MIT, copyright 2026 Israel Orere. Narrative and original plots: CC BY 4.0, with underlying data attributions preserved.

## Re-run

Install Python 3.12+ with numpy, pandas, pyarrow, shapely and matplotlib. Set ZINDI_DATA_DIR to a folder with the manifest-listed challenge files. Unzip the evidence bundle, then run the included scripts from the extracted project root. Saved OSM extracts are reused. run_discovery.py rebuilds per-site comparisons; analyze_discovery.py combines regional tables; audit_name_displacements.py rebuilds the exact-name diagnostic; render_figures.py redraws the original figures; build_story_overview.py draws the simplified regional rural/urban chart and exports its exact counts. build_wildfire_story.py adds the descriptive exposure-group chart and exports every group and its rural/urban composition from the existing equity table; it fits no new model. This display was added on 27 October 2026, after the earlier equity findings. Exposure groups use existing within-region tract ranks, not station-count quantiles. The model's 25th-to-75th-percentile contrast is distinct from the unadjusted group-average differences. Map extracts are archived; fetch_map_layers.py is needed only for re-querying their public sources. build_report.py rebuilds the readable report from work/story_writeup.md.
'''
if (OUT/'equity_analysis_results.json').exists():
    method+='''\n## Equity follow-up\n\nThe equity analysis uses the existing OSM fire sites and supplied tract strata; it does not introduce new reference targets. See equity_followup_report.html for the evidence and equity_analysis_results.json for the written analysis plan. The primary outcome is compatible-category correspondence within 100 m of OSM geometry, with 50/200 m sensitivity. Rurality, national 2022 SVI, regional wildfire-exposure percentiles and tribal-area overlap are compared with all denominators retained. Tribal overlap is area, not residents' identity; legal and statistical geographies are kept distinct. CVI vintage 2010 identifies its source tract geography, not the date of every index observation.\n\nSupplemental linear probability models include region effects, population, observed site supply, SVI, wildfire/heat/drought ranks, followed by polygon geometry, GNIS tags, map-object age, name presence and station numbering; density is a separate sensitivity because it overlaps with rurality. Standard errors cluster by county. These are adjusted associations, not causal effects or confirmed error rates. Matching uses only covariates and exact region/site supply; the initial 166 pairs retain exposure imbalance, while stricter exploratory comparisons retain only 97 or 62 pairs. The most exposed rural tracts lack comparable urban observations and should not be generalized from the retained matches. Bootstrap uncertainty for matched pairs clusters by rural county only. All planned subgroup results, sparse cells, nulls and reversals are distributed.\n\nThe explicit follow-up plan labels stricter matching, burn probability, region-specific model coefficients and additional hazard sensitivities as exploratory after viewing the initial equity results. No multiplicity-adjusted confirmatory inference is claimed. The landscape Exposure Type index is distinct from burn probability, housing-weighted exposure, station-site hazard and current danger. Tract population is contextual, not a station catchment or number of people harmed. A tract with no OSM station has no comparator station and is not treated as a service desert or fully covered.\n\nReproduce the equity follow-up after the base comparison with: python work/analyze_equity.py; python work/equity_followup_checks.py; python work/build_equity_report.py; python work/build_report.py. scipy is an additional open-source dependency. See equity_validation.json for integrity checks and source URLs.\n'''
(OUT/'methodology.md').write_text(method,encoding='utf-8')
# Render a compact, local HTML reading copy with embedded figures.
import base64
def esc(s):return html.escape(s)
def md_inline(s):
    s=esc(s);s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<em>\1</em>',s)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)]+|[a-z_]+\.(?:html|md|zip))\)',r'<a href="\2">\1</a>',s)
parts=[];in_table=False
for chunk in article.split('\n\n'):
    if chunk.startswith('!['):
        m=re.match(r'!\[([^]]*)\]\(([^)]+)\)',chunk)
        imagepath=OUT/m[2];data=base64.b64encode(imagepath.read_bytes()).decode()
        parts.append(f'<figure><img alt="{esc(m[1])}" src="data:image/png;base64,{data}"><figcaption>{esc(m[1])}</figcaption></figure>')
    elif chunk.startswith('|'):
        lines=chunk.splitlines();head=lines[0];body=lines[2:]
        parts.append('<div class="table"><table><thead><tr>'+''.join('<th>'+md_inline(c.strip())+'</th>' for c in head.strip('|').split('|'))+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+md_inline(c.strip())+'</td>' for c in line.strip('|').split('|'))+'</tr>' for line in body)+'</tbody></table></div>')
    elif re.match(r'^\d+\.\s',chunk):
        items=[re.sub(r'^\d+\.\s+','',line) for line in chunk.splitlines() if line.strip()]
        parts.append('<ol class="reading-guide">'+''.join('<li>'+md_inline(item)+'</li>' for item in items)+'</ol>')
    elif chunk.startswith('# '):parts.append('<h1>'+esc(chunk[2:])+'</h1>')
    elif chunk.startswith('## '):parts.append('<h2>'+esc(chunk[3:])+'</h2>')
    else:parts.append('<p>'+md_inline(chunk).replace('\n',' ')+'</p>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>The Map Says Empty. The Community Is Not.</title><style>body{margin:0;background:#f8f6ef;color:#18352e;font:18px/1.65 Georgia,serif}main{max-width:1050px;padding:48px 28px;margin:auto}h1{font:700 clamp(36px,5vw,66px)/1.08 system-ui;max-width:850px;letter-spacing:-.045em}h2{font:650 27px/1.25 system-ui;margin-top:45px}p{max-width:850px}a{color:#15786e}strong{font-weight:700}figure{margin:32px -10px}img{width:100%;height:auto;display:block}figcaption{font:12px/1.5 system-ui;color:#62756c;margin:8px 10px}table{border-collapse:collapse;font:14px/1.4 system-ui;width:100%}th,td{text-align:left;padding:14px;border-bottom:1px solid #d7ded5}th{background:#e8ede4}.table{overflow:auto}footer{font:13px/1.6 system-ui;border-top:1px solid #d7ded5;padding-top:25px;margin-top:45px}@media print{body{font-size:11pt}main{padding:10px}h1{font-size:30pt}figure,table{break-inside:avoid}}</style><main>'''+''.join(parts)+f'<footer>Read the <a href="methodology.md">method and limitations</a>, <a href="facility_audit.csv">facility audit</a> and <a href="named_case_evidence.json">named record evidence</a>. Source rules: <a href="{rules}">Zindi Best Bias Discovery</a>. Additional public data are used for discovery only.</footer></main></html>'
page=page.replace('<title>The Map Says Empty. The Community Is Not.</title>', '<title>'+esc(article_title)+'</title>')
page=page.replace('</style>', '.reading-guide{max-width:800px;padding:20px 24px 20px 48px;background:#e8ede4;border-left:4px solid #15786e;font:16px/1.6 system-ui}.reading-guide li+li{margin-top:12px}</style>')
(OUT/'bias_discovery_visual_report.html').write_text(page,encoding='utf-8')
print('Report built:',len(f),'fire sites,',len(regions),'regions;',recurs,'rural disadvantages',flush=True)
