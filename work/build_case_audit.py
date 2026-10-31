from run_discovery import *
from shapely.geometry import shape
import html,base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon
from shapely.ops import transform
decisions=json.loads((ROOT/'work/case_decisions.json').read_text())
context={c['name']:c for c in json.loads((ROOT/'work/full_case_context.json').read_text())}
pairs=pd.read_csv(OUT/'exact_name_location_audit.csv',dtype={'GEOID':str,'destination_GEOID':str},keep_default_na=False)
fac=pd.read_csv(OUT/'facility_audit.csv',dtype={'GEOID':str},keep_default_na=False)
physical={c['name']:c for c in json.loads((OUT/'reviewed_case_physical_checks.json').read_text())}
BG='#f8f6ef';INK='#18352e';RED='#b6462d';GREEN='#16796c';BLUE='#375c9a'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9})
def cats(p):
    c=p.get('categories') or {};return set([c.get('primary')]+(c.get('alternate') or []))
def draw(ax,g,fn,**kw):
    g=transform(fn,g)
    if g.geom_type=='Polygon':ax.add_patch(PatchPolygon(np.array(g.exterior.coords),**kw))
    elif g.geom_type in ['MultiPolygon','GeometryCollection']:
        for sub in g.geoms:
            if sub.geom_type=='Polygon':ax.add_patch(PatchPolygon(np.array(sub.exterior.coords),**kw))
layers={}
def plot_case(d,c):
    region=c['region'];tag='_mesa' if region=='maricopa-az' else '_all_ten'
    if region not in layers:layers[region]={k:json.loads((ROOT/'work'/f'{region}{tag}_{k}_map.geojson').read_text())['features'] for k in ['buildings','roads']}
    fig,axs=plt.subplots(1,2,figsize=(8.4,3.45));fig.patch.set_facecolor(BG)
    for ax,(label,geom,title) in zip(axs,[('osm_site',c['osm']['geometry'],'OSM site · supplied Overture surroundings'),('overture_site',c['overture']['geometry'],'Same-name Overture record · surroundings')]):
        g=shape(geom);p=g.representative_point();cos=math.cos(math.radians(p.y));fn=lambda x,y,z=None:((np.asarray(x)-p.x)*111320*cos,(np.asarray(y)-p.y)*111320)
        ax.set_facecolor(BG)
        for b in layers[region]['buildings']:
            bg=shape(b['geometry'])
            if bg.distance(p)<.004:draw(ax,bg,fn,facecolor='#d8ddd6',edgecolor='#a9b2a7',linewidth=.4)
        for road in layers[region]['roads']:
            rg=shape(road['geometry'])
            if rg.distance(p)<.004:
                lines=rg.geoms if rg.geom_type=='MultiLineString' else [rg]
                for ln in lines:
                    if ln.geom_type=='LineString':ax.plot(*transform(fn,ln).xy,color='#b9ac88',lw=1.4,zorder=1)
        for rec in c['nearby'][label]:
            if 'fire_department' in cats(rec):
                pt=shape(rec['geometry']);x,y=fn(pt.x,pt.y)
                if abs(x)<170 and abs(y)<170:ax.scatter([x],[y],marker='^',s=75,c=GREEN,edgecolor='white',zorder=6)
        if label=='osm_site':
            if g.geom_type in ['Polygon','MultiPolygon']:draw(ax,g,fn,facecolor='none',edgecolor=RED,linewidth=1.7,zorder=7)
            ax.scatter([0],[0],marker='x',c=RED,s=65,linewidths=1.6,zorder=8)
        else:ax.scatter([0],[0],marker='D',facecolor='none',edgecolor=BLUE,s=90,linewidths=1.8,zorder=8)
        ax.plot([-145,-45],[-143,-143],color=INK,lw=2.5);ax.text(-95,-133,'100 m',ha='center',fontsize=8,color=INK)
        ax.text(145,142,'N ↑',ha='right',fontsize=8,color=INK)
        ax.set(xlim=(-170,170),ylim=(-170,170),aspect='equal',xticks=[],yticks=[])
        ax.set_title(title,fontsize=9,loc='left',color=INK,pad=8)
        for spine in ax.spines.values():spine.set_edgecolor('#d8dacf')
    fig.text(.03,.035,'Red × / outline: OSM site   •   Green ▲: compatible Overture fire place   •   Blue ◇: screened same-name record',fontsize=8,color=INK)
    fig.subplots_adjust(left=.025,right=.985,top=.89,bottom=.12,wspace=.08)
    path=OUT/f"case_{d['key']}.png";fig.savefig(path,dpi=150,facecolor=BG);plt.close(fig);return path
reviews=[]
for d in decisions:
    c=context[d['name']];p=pairs[pairs.osm_name==d['name']].iloc[0].to_dict();f=fac[fac.osm_id==p['osm_id']].iloc[0].to_dict();checks=physical[d['name']]
    localfire=[x for x in c['nearby']['osm_site'] if 'fire_department' in cats(x)]
    r={**d,'region':c['region'],'distance_km':c['distance_km'],'same_tract':c['same_tract'],'origin_tract':p['GEOID'],'destination_tract':p['destination_GEOID'],'rurality':p['ur_class'],'overture_primary_category':p['overture_primary'],'overture_confidence':p['overture_confidence'],'root_source':p['source'],'osm_id':p['osm_id'],'osm_timestamp':f['osm_timestamp'],'overture_id':p['overture_id'],'osm_tags':json.loads(c['osm']['properties']['osm_tags']),'osm_geometry':c['osm']['geometry'],'overture_record':c['overture'],'physical_checks':checks['sites'],'nearby_compatible_fire_places_350m':localfire,'compatible_fire_place_within_200m':bool(f['compatible_200m']),'nearby_all_places_350m_count':len(c['nearby']['osm_site']),'interpretation_date':'2026-10-24','osm_snapshot':DATE,'overture_release':'2026-08-19.0'}
    if d['key']=='westport':
        adr=json.loads((ROOT/'work/review_sources/westport_official_address_query.json').read_text())['features'][0]
        point=Point(adr['geometry']['x'],adr['geometry']['y']);r['county_address_point_distance_to_osm_m']=distance(point,shape(c['osm']['geometry']),point.y)
    path=plot_case(d,c);r['figure']=path.name;reviews.append(r)
(OUT/'case_review_ledger.json').write_text(json.dumps(reviews,indent=2),encoding='utf-8')
csvrows=[]
for r in reviews:
    row={k:r[k] for k in ['name','region','rurality','distance_km','verdict','label','confidence','osm_id','osm_timestamp','overture_id','overture_primary_category','overture_confidence','root_source','origin_tract','destination_tract','same_tract','compatible_fire_place_within_200m','finding','interpretation','next_check']}
    for end in ['osm','overture']:
        row[end+'_point_inside_overture_building']=r['physical_checks'][end]['point_inside_building']
        row[end+'_overlapping_overture_buildings']=r['physical_checks'][end]['overlapping_buildings']
        row[end+'_nearest_supplied_road_m']=r['physical_checks'][end]['nearest_road_m']
    row['other_compatible_fire_places_350m']='; '.join(f"{p['name']} ({p['distance_from_site_m']:.1f} m)" for p in r['nearby_compatible_fire_places_350m'])
    row['source_urls']=' | '.join(s['url'] for s in r['sources']);csvrows.append(row)
pd.DataFrame(csvrows).to_csv(OUT/'case_review_ledger.csv',index=False)
counts=dict(collections.Counter(r['verdict'] for r in reviews));thresholds={str(t):int((pairs.distance_m>t).sum()) for t in [100,200,500,1000,5000,10000]}
summary={'reviewed_cases':len(reviews),'original_cases':10,'additional_arizona_cases':1,'verdict_counts':counts,'unique_name_pairs_screened':len(pairs),'distance_threshold_counts':thresholds,'review_rule':'Every unique-name pair above 500 m in the four completed regions was adjudicated. Seven additional 100–500 m pairs are listed as threshold diagnostics, not verified errors.','completed_regions':sorted(fac.region.unique()),'fire_sites':int((fac.facility_type=='fire').sum()),'uncompleted_region':'south-central-tx','interpretation':'Selected cases demonstrate recurrence, not an error prevalence or causal rurality effect.'}
(OUT/'case_review_summary.json').write_text(json.dumps(summary,indent=2))
esc=lambda s:html.escape(str(s))
def link(s):return f'<a href="{esc(s["url"])}" target="_blank" rel="noreferrer">{esc(s["title"])}</a><small>{esc(s["access"])}</small>'
def image_tag(path,alt):return f'<img alt="{esc(alt)}" src="data:image/png;base64,{base64.b64encode(path.read_bytes()).decode()}">'
cards=[];md=['# Full case review: where the fire-station identity belongs','',f"Reviewed 24 October 2026. All {len(reviews)} exact-name separations above 500 m in the four completed regions were reviewed: 3 supported location errors, 5 distinct-facility pairings, 3 unresolved. The ten original cases plus one Arizona case are included. These are selected candidates, not a random sample or an error-rate estimate.",'']
for i,r in enumerate(reviews,1):
    address='; '.join(', '.join(str(a.get(k) or '') for k in ['freeform','locality','region','postcode']) for a in r['overture_record']['addresses'] or [])
    local='; '.join(f"{p['name']} ({p['distance_from_site_m']:.1f} m from OSM geometry)" for p in r['nearby_compatible_fire_places_350m']) or 'None within the 350 m context search'
    facts=f"{r['rurality']} · {r['region']} · {r['distance_km']:.3f} km point separation · {'same tract' if r['same_tract'] else 'different tracts'}"
    sources=''.join('<li>'+link(s)+'</li>' for s in r['sources'])
    geometry='; '.join(f"{label}: representative point {'inside' if r['physical_checks'][end]['point_inside_building'] else 'outside'} supplied footprints, {r['physical_checks'][end]['overlapping_buildings']} intersecting building(s), nearest supplied road {r['physical_checks'][end]['nearest_road_m']:.1f} m" for end,label in [('osm','OSM site'),('overture','named-record site')])
    cards.append(f'''<article class="case {esc(r['verdict'])}" id="{r['key']}" data-verdict="{r['verdict']}"><div class="casehead"><span class="number">{i:02}</span><div><span class="tag">{esc(r['label'])}</span><h2>{esc(r['name'])}</h2><p class="facts">{esc(facts)}</p></div></div><p>{esc(r['finding'])}</p>{image_tag(OUT/r['figure'],r['name']+' — two equal-scale endpoint maps')}<div class="interpret"><strong>Assessment</strong><p>{esc(r['interpretation'])}</p></div><p><strong>Evidence strength:</strong> {esc(r['confidence'])}.</p><p><strong>Next step:</strong> {esc(r['next_check'])}</p><details><summary>Inspect identifiers, map checks and sources</summary><dl><dt>OSM object / last object edit</dt><dd><a href="https://www.openstreetmap.org/{r['osm_id']}">{esc(r['osm_id'])}</a> · {esc(r['osm_timestamp'])}</dd><dt>Overture screened record</dt><dd>{esc(r['overture_id'])}</dd><dt>Record address</dt><dd>{esc(address)}</dd><dt>Category / confidence / root source</dt><dd>{esc(r['overture_primary_category'])} · {r['overture_confidence']:.4f} · {esc(r['root_source'])}</dd><dt>Tracts: OSM site → named record</dt><dd>{esc(r['origin_tract'])} → {esc(r['destination_tract'])}</dd><dt>Compatible fire places near OSM site</dt><dd>{esc(local)}</dd><dt>Physical checks</dt><dd>{esc(geometry)}. Footprints and roads are mapping evidence, not operational-status proof.</dd></dl><ol class="sources">{sources}</ol></details></article>''')
    md.extend([f"## {i}. {r['name']}",'',f"**{r['label']}** — {facts}",'',r['finding'],'',r['interpretation'],'',f"Evidence strength: {r['confidence']}.",'',f"Next step: {r['next_check']}",'',f"Local compatible fire places: {local}.",'',f"OSM {r['osm_id']}; Overture {r['overture_id']}; confidence {r['overture_confidence']:.4f}; root source {r['root_source']}.",'',f"![Equal-scale endpoint maps]({r['figure']})",'']+[f"- [{s['title']}]({s['url']}) — {s['access']}" for s in r['sources']]+[''])
medium=pairs[(pairs.distance_m>100)&(pairs.distance_m<=500)].sort_values('distance_m',ascending=False)
mediumrows=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in [p.osm_name,p.region,f'{p.distance_m:.1f} m',p.ur_class])+'</tr>' for p in medium.itertuples())
method=f'''<section class="scope"><h2>What “comprehensive” covers here</h2><p>The full proximity comparison covers {summary['fire_sites']:,} OSM fire sites in four complete data-package regions. The exact-name screen contains {len(pairs)} unique normalized-name pairs; every pair above 500 m is adjudicated above. Names must be unique on both sides within a region, and generic labels are excluded. This precision-focused screen cannot detect unnamed facilities, all aliases, duplicate department names, missing records with no name counterpart, or records outside the supplied extract.</p><p>At 100 m the exact-name screen flags {thresholds['100']} pairs; at 200 m, {thresholds['200']}; at 500 m, {thresholds['500']}. Seven additional 100–500 m differences appear below. They were screened computationally, not independently adjudicated, and must not be counted as verified errors. The main correspondence analysis separately tests 50, 100 and 200 m using distance to OSM geometry.</p><div class="table"><table><thead><tr><th>100–500 m diagnostic</th><th>Region</th><th>Point separation</th><th>Tract class</th></tr></thead><tbody>{mediumrows}</tbody></table></div><p>Texas historical retrieval remains incomplete after large queries, four tiles and smaller subtiles. Its partial results are excluded from rates and candidate totals. Eastern Washington is supplementary; it is not one of the four leaderboard regions. Additional unnamed/alias-based case discovery and operational verification of every unmatched site remain outside this completed review.</p><p>All supplied Overture places within 350 m of each reviewed endpoint were inspected for compatible fire categories, including alternate categories. The named record is not assumed to be the only representation of a facility. OSM object history was reviewed for the original ten cases; a last-edit timestamp dates the map object, not the facility. Current official pages may postdate the snapshot; explicit dated evidence is used where available. No field visits or department contacts were made.</p><p>The original Adair school lead was also checked: Bell, Zion and Peavine are present; Bell's point offset alone is not an omission. Oak Ridge's operational status remains unverified. That abandoned lead is retained in the methodology to prevent its reuse as evidence.</p><p>Maps use the challenge's supplied Overture buildings and roads. Those layers can share upstream OSM data; overlap establishes cross-layer retention, not independent real-world verification. Endpoint panels show equal 340 m windows and are separated by the stated point-to-point distance, not travel distance. Roads may be filtered in the supplied extract. Blank map space does not prove a missing real-world building or road.</p><p>Overture release 2026-08-19.0; OSM historical state 2026-08-01 00:00 UTC. Case review: 24 October 2026. Additional public sources inform discovery only. No withdrawn target/reference layers or new scored predictions were used.</p></section>'''
style='''body{margin:0;background:#f8f6ef;color:#18352e;font:17px/1.65 Georgia,serif}main{max-width:1030px;margin:auto;padding:44px 24px}h1,h2,h3,button,.tag,.facts,.number,summary,dt,th,footer{font-family:system-ui,sans-serif}h1{font-size:clamp(38px,6vw,66px);line-height:1.06;letter-spacing:-.04em;max-width:900px}h2{font-size:25px;line-height:1.25;margin:8px 0}a{color:#15786e}p{max-width:920px}.eyebrow{font:600 12px system-ui;letter-spacing:.1em;text-transform:uppercase;color:#65796c}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:28px 0}.stat{padding:18px;background:#e8ede4;border-radius:9px;font:13px system-ui}.stat b{display:block;font-size:36px;line-height:1.2}.filters{display:flex;gap:8px;flex-wrap:wrap;position:sticky;top:0;background:#f8f6eff5;padding:14px 0;z-index:20}button,input{border:1px solid #b6c3b6;border-radius:20px;background:white;padding:9px 14px;color:#18352e;font:13px system-ui}button{cursor:pointer}button.active{background:#18352e;color:white}input{min-width:180px;flex:1}.case{padding:30px 0;border-top:1px solid #ced6c9}.casehead{display:flex;gap:18px}.number{font-size:35px;font-weight:300;color:#a4b0a2}.tag{font-size:12px;font-weight:650;letter-spacing:.03em;color:#68735a}.supported_location_error .tag{color:#b6462d}.distinct_facilities .tag{color:#15786e}.unresolved .tag{color:#8b6835}.facts{font-size:13px;color:#607164;margin:6px 0}img{width:100%;height:auto;margin:12px 0}.interpret{border-left:3px solid #b6c3b6;padding:10px 18px;background:#edf0e7}.interpret p{margin:3px 0}.supported_location_error .interpret{border-color:#b6462d}details{background:#f0f1e8;border-radius:8px;padding:16px 20px;font-size:14px}summary{cursor:pointer;font-size:14px;font-weight:600}dl{display:grid;grid-template-columns:230px 1fr;gap:10px 20px}dt{font-weight:600}dd{margin:0;overflow-wrap:anywhere}small{display:block;font:12px/1.5 system-ui;color:#697a6c}.sources li{margin:14px 0}.scope{margin:35px 0}.table{overflow:auto}table{border-collapse:collapse;width:100%;font:13px/1.5 system-ui}td,th{padding:11px;text-align:left;border-bottom:1px solid #d5ddcf}.note{font:14px/1.6 system-ui;color:#657366}footer{padding-top:25px;border-top:1px solid #ced6c9;font-size:12px}[hidden]{display:none!important}@media(max-width:650px){.stats{grid-template-columns:1fr 1fr}dl{grid-template-columns:1fr;gap:4px}dd{margin-bottom:12px}.filters{position:static}}@media print{.filters{display:none}.case{break-inside:avoid}details{display:block}main{padding:0}h1{font-size:30pt}}'''
js='''let chosen='all';const buttons=[...document.querySelectorAll('button[data-filter]')],search=document.getElementById('search');function filter(){let shown=0;document.querySelectorAll('.case').forEach(c=>{const show=(chosen==='all'||c.dataset.verdict===chosen)&&c.textContent.toLowerCase().includes(search.value.toLowerCase());c.hidden=!show;shown+=show});document.getElementById('visible').textContent=shown+' cases shown'}buttons.forEach(b=>b.onclick=()=>{chosen=b.dataset.filter;buttons.forEach(x=>x.classList.toggle('active',x===b));filter()});search.oninput=filter;'''
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fire-station location audit — all 11 cases</title><style>{style}</style></head><body><main><p class="eyebrow">Best Bias Discovery · full evidence review · 24 October 2026</p><h1>A long distance is a clue. The case still needs proof.</h1><p>We reviewed the ten original flags and the additional Arizona flag. <strong>Three cases support location errors</strong>; five compare distinct facilities, and three remain unresolved. Correct local Overture records invalidate three of the apparent errors. Two other cases raise branch-coverage questions. This review documents the evidence, alternatives and exclusions for every case.</p><div class="stats"><div class="stat"><b>11</b>cases adjudicated</div><div class="stat"><b>3</b>supported location errors</div><div class="stat"><b>5</b>distinct-facility pairings</div><div class="stat"><b>3</b>unresolved cases</div></div><p class="note">The three supported examples are Porum (rural Oklahoma), Westport (rural California), and Broken Arrow (urban Oklahoma). They demonstrate recurrence across two regions. Selected cases cannot establish a rural error rate or a causal bias mechanism. “Supported” means corroborated by the cited desktop evidence, with case-specific caveats.</p><p><a href="bias_discovery_visual_report.html">Read the short visual report</a> · <a href="case_review_ledger.csv">Download the verdict table</a> · <a href="case_review_ledger.json">Detailed evidence</a> · <a href="exact_name_location_audit.csv">All {len(pairs)} screened name pairs</a></p><nav class="filters" aria-label="Filter reviewed cases"><button class="active" data-filter="all">All 11</button><button data-filter="supported_location_error">Supported 3</button><button data-filter="distinct_facilities">Distinct facilities 5</button><button data-filter="unresolved">Unresolved 3</button><input id="search" aria-label="Search cases" placeholder="Search case or place…"></nav><p class="note" id="visible">11 cases shown</p>{''.join(cards)}{method}<footer>© OpenStreetMap contributors, ODbL. Overture/provider attribution retained in the evidence ledger; maps use supplied Overture extracts. Analysis and original figures: Israel Orere, 2026. Read <a href="methodology.md">methodology and limitations</a>. This HTML embeds its images and works offline; source links require internet.</footer></main><script>{js}</script></body></html>'''
(OUT/'comprehensive_case_audit.html').write_text(page,encoding='utf-8')
(OUT/'comprehensive_case_audit.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
