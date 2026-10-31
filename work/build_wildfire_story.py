"""Descriptive exposure deep dive, using the existing analysis and model outputs.

Added 27 October for explanation. No new model is selected or fitted here.
Exposure bands use the existing within-region tract ranks, independently of outcomes.
"""
from run_discovery import OUT, pd, np, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import Patch

f = pd.read_csv(OUT/'equity_fire_site_analysis.csv', dtype={'GEOID':str})
bands = ['Lowest exposure quarter', 'Middle half', 'Highest exposure quarter']
f['exposure_group'] = pd.cut(f.wildfire_rank, [-np.inf,.25,.75,np.inf], labels=bands)
assert f.exposure_group.notna().all()
rows = []
for (region, band), g in f.groupby(['region','exposure_group'], observed=True):
    rows.append({'region':region,'exposure_group':band,'sites':len(g),
                 'tracts':g.GEOID.nunique(),'matched':int(g.compatible_100m.sum()),
                 'percent':100*float(g.compatible_100m.mean()),
                 'rural_sites':int(g.ur_class.eq('Rural').sum()),
                 'urban_sites':int(g.ur_class.eq('Urban').sum()),
                 'unknown_rurality_sites':int((~g.ur_class.isin(['Rural','Urban'])).sum())})
rates = pd.DataFrame(rows)
assert rates.sites.sum()==1372 and len(rates)==12
rates.to_csv(OUT/'wildfire_story_exposure_groups.csv', index=False)

# Retain all rural/urban cells too; the figure must not conceal their different composition.
composition = f.groupby(['region','ur_class','exposure_group'],dropna=False,observed=True).agg(
    sites=('osm_id','size'),matched=('compatible_100m','sum')).reset_index()
composition['percent'] = 100*composition.matched/composition.sites
composition.to_csv(OUT/'wildfire_story_group_composition.csv',index=False)

models = pd.read_csv(OUT/'equity_wildfire_association_sensitivity.csv')
main = models[models.model.eq('Exposure Type, all regions')].iloc[0]
rural = pd.read_csv(OUT/'equity_adjusted_associations.csv')
baseline = rural[rural.model.eq('Region only') & rural.term.eq('rural')].iloc[0]
adjusted = rural[rural.model.eq('Region + community need/supply') & rural.term.eq('rural')].iloc[0]
summary = {
    'added':'2026-10-27',
    'purpose':'Plain-language descriptive deep dive; no new inferential test or model fitting',
    'sites':len(f),'groups':12,
    'group_definition':'Existing wildfire_rank from all supplied tracts within region: <=0.25, >0.25 and <=0.75, >0.75. Each station inherits its tract rank; groups are not equal-sized samples of stations.',
    'exposure_definition':'Tract landscape Exposure Type average, related to proximity to burnable vegetation; not annual burn probability, station-site danger or a current forecast.',
    'all_lowest_quarter_sites_urban':bool(rates.loc[rates.exposure_group.eq(bands[0]),'rural_sites'].sum()==0 and rates.loc[rates.exposure_group.eq(bands[0]),'unknown_rurality_sites'].sum()==0),
    'rural_region_adjusted_gap_pp':-float(baseline.coefficient_pp),
    'rural_community_adjusted_gap_pp':-float(adjusted.coefficient_pp),
    'rural_community_adjusted_coefficient_interval_pp':[float(adjusted.ci_low_pp),float(adjusted.ci_high_pp)],
    'wildfire_25th_to_75th_rank_adjusted_gap_pp':-float(main.association_per_rank_iqr_pp),
    'wildfire_adjusted_gap_interval_pp':[-float(main.ci_high_pp),-float(main.ci_low_pp)],
    'model_sites':int(main.sites),'county_clusters':int(main.counties),
    'interpretation':'Expected difference in local-match share from a statistical model, not observed lost stations, an operating-station omission rate, or a causal wildfire effect.',
    'important_overlap_limit':'Lowest exposure quarter contains no rural sites in this sample. Adjustment relies on a model and does not create directly comparable rural/urban observations at every exposure level.',
}
(OUT/'wildfire_story_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')

bg,ink,muted='#f8f6ef','#18352e','#586d63'
colors=['#d8b476','#be7a42','#94402b']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
fig, axs = plt.subplots(2,2,figsize=(12.4,9.7),facecolor=bg)
regions=[('eastern-ok','Eastern Oklahoma'),('eastern-wa','Eastern Washington (supplementary)'),
         ('maricopa-az','Maricopa + surrounding area'),('northern-ca','Northern California')]
fig.text(.065,.957,'A SECOND PATTERN: WILDFIRE EXPOSURE',fontsize=11,weight='bold',color=muted)
fig.text(.065,.910,'More exposed places have fewer nearby listings.',fontsize=24,weight='bold',color=ink)
fig.text(.065,.865,'Share of station sites with a fire-department listing within 100 metres.',fontsize=12,color=ink)
legend_labels=['Least exposed\nBottom 25% of areas','Middle exposure\nMiddle 50% of areas','Most exposed\nTop 25% of areas']
fig.legend(handles=[Patch(facecolor=color,label=label) for color,label in zip(colors,legend_labels)],
           loc='upper left',bbox_to_anchor=(.065,.827),ncol=3,frameon=False,
           fontsize=12,handlelength=1.4,handleheight=1.6,columnspacing=3.3,
           borderaxespad=0,labelcolor=ink)
for ax,(region,label) in zip(axs.flat,regions):
    ax.set_facecolor(bg)
    group=rates[rates.region.eq(region)].set_index('exposure_group').loc[bands]
    ax.bar(range(3),group.percent,width=.54,color=colors,zorder=3)
    for i,row in enumerate(group.itertuples()):
        ax.text(i,row.percent-2.8,f'{row.percent:.0f}%',ha='center',va='top',fontsize=17,weight='bold',color='white' if i==2 else ink)
        ax.text(i,row.percent+3.3,f'{row.matched} / {row.sites} sites',ha='center',va='bottom',fontsize=10,color=muted)
    ax.set_ylim(0,114)
    ax.set_xlim(-.6,2.6)
    ax.set_yticks([0,25,50,75,100])
    ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_xticks(range(3),['Least\nexposed','Middle\nexposure','Most\nexposed'])
    ax.tick_params(axis='both',length=0,labelsize=10,colors=muted,pad=7)
    ax.grid(axis='y',color='#dce1d6',linewidth=.7,zorder=0)
    ax.set_title(label,loc='left',fontsize=14,weight='bold',color=ink,pad=13)
    for spine in ax.spines.values():spine.set_visible(False)
fig.subplots_adjust(left=.09,right=.96,top=.715,bottom=.145,wspace=.26,hspace=.55)
fig.text(.065,.064,'Exposure is based on surrounding burnable vegetation. Groups are ranked within each region.',fontsize=10,color=muted)
fig.text(.065,.025,'Sources: Overture 2026-08-19.0 · © OpenStreetMap contributors, historical state 2026-08-01',fontsize=8,color=muted)
for extension in ['png','svg']:
    fig.savefig(OUT/f'wildfire_story_overview.{extension}',dpi=180,facecolor=bg)
plt.close(fig)
notes_path=OUT/'story_evidence_notes.json'
notes=json.loads(notes_path.read_text(encoding='utf-8'))
notes['narrative_order'][2]='Discovery-led wildfire deep dive with observed group rates and the adjusted association; full qualifications linked in article_analysis_notes.md'
notes['reader_guide']='Lead with three discoveries: the rural/urban listing gap, the wildfire-exposure association and supported building/listing location mismatches.'
notes['qualification_placement']='One short interpretation note at the end of the article, with complete qualifications in article_analysis_notes.md and the full equity and case reports.'
notes['wildfire_deep_dive']={
    'added':'2026-10-27',
    'figure':'wildfire_story_overview.png',
    'data':'wildfire_story_exposure_groups.csv',
    'composition':'wildfire_story_group_composition.csv',
    'scope':'Descriptive presentation added after the earlier analysis; all 12 region/exposure cells disclosed; no new model fitted',
    'key_limits':'Raw groups differ in rurality; no rural sites in lowest quarter; adjusted 25th-to-75th-rank contrast is not the group-average contrast; no causal or confirmed-omission claim',
    'display_labels':'Least exposed = bottom 25% of regional tract ranks; middle exposure = middle 50%; most exposed = top 25%. Colours have a matching legend.',
}
notes_path.write_text(json.dumps(notes,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
