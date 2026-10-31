"""Present the existing regional comparison without changing its definition."""
from run_discovery import ROOT, OUT, pd, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

order = [
    ('eastern-ok', 'Eastern\nOklahoma'),
    ('eastern-wa', 'Eastern\nWashington*'),
    ('maricopa-az', 'Maricopa +\nsurrounding area'),
    ('northern-ca', 'Northern\nCalifornia'),
]
source = pd.concat([
    pd.read_csv(OUT / f'{region}_facility_audit.csv') for region, _ in order
], ignore_index=True)
source = source[source.facility_type.eq('fire')]
rows = []
for region, _ in order:
    for group in ['Rural', 'Urban']:
        subset = source[source.region.eq(region) & source.ur_class.eq(group)]
        matched = int(subset.compatible_100m.sum())
        rows.append(dict(region=region, group=group, sites=len(subset),
                         nearby_listings=matched, percent=100 * matched / len(subset)))
rates = pd.DataFrame(rows)
rates.to_csv(OUT / 'rural_urban_story_chart_data.csv', index=False)

bg, ink, muted = '#f8f6ef', '#18352e', '#586d63'
colors = {'Rural': '#b2472e', 'Urban': '#15786e'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12})
fig = plt.figure(figsize=(12.2, 8.8), facecolor=bg)
ax = fig.add_axes([.335, .245, .405, .52], facecolor=bg)
fig.text(.055, .945, 'THE RURAL–URBAN GAP', color=muted, fontsize=11, weight='bold')
fig.text(.055, .889, 'Rural fire-station sites are less often listed nearby.',
         fontsize=22, weight='bold', color=ink)
fig.text(.055, .839, 'The same pattern appears in all four regions we checked.',
         fontsize=14, color=ink)
fig.text(.78, .79, 'WITH A NEARBY LISTING', fontsize=9, color=muted, weight='bold')
fig.text(.885, .765, 'matched / checked', fontsize=9, color=muted)

for i, (region, label) in enumerate(order):
    center = 6.7 - 2 * i
    # Row labels and numbers are in figure space so they stay aligned.
    fy = .245 + .52 * ((center + .6) / 8)
    fig.text(.055, fy, label, ha='left', va='center', fontsize=14, weight='bold', color=ink)
    for group, delta in [('Rural', .30), ('Urban', -.30)]:
        row = rates[rates.region.eq(region) & rates.group.eq(group)].iloc[0]
        y = center + delta
        ax.barh(y, 100, height=.35, color='#e4e7df', zorder=1)
        ax.barh(y, row['percent'], height=.35, color=colors[group], zorder=3)
        ax.text(-5, y, group, ha='right', va='center', fontsize=12, color=colors[group])
        row_fy = .245 + .52 * ((y + .6) / 8)
        fig.text(.79, row_fy, f"{row['percent']:.0f}%", va='center',
                 fontsize=18, weight='bold', color=colors[group])
        fig.text(.885, row_fy, f"{row['nearby_listings']:,} / {row['sites']:,}",
                 va='center', fontsize=12, color=ink)

ax.set_xlim(0, 100)
ax.set_ylim(-.6, 7.4)
ax.set_yticks([])
ax.set_xticks([0, 25, 50, 75, 100])
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.tick_params(axis='x', labelsize=10, colors=muted, length=0, pad=9)
ax.set_axisbelow(True)
ax.grid(axis='x', color='#d4dcd1', linewidth=.7)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_xlabel('Share of checked sites with a nearby listing', fontsize=11, color=ink, labelpad=14)
fig.text(.055, .145, 'What we checked', fontsize=11, weight='bold', color=ink)
fig.text(.055, .111, 'OpenStreetMap fire-station sites with an Overture fire-department listing within 100 metres.',
         fontsize=11, color=ink)
fig.text(.055, .078, 'Each bar measures agreement between the two sets of map records, using the same 100-metre check.',
         fontsize=10, color=muted)
fig.text(.055, .042, '*Washington is supplementary; Texas is excluded. One site with unknown rurality is not shown.',
         fontsize=9, color=muted)
fig.text(.055, .016, 'Overture 2026-08-19.0 · © OpenStreetMap contributors, 2026-08-01 historical state · Chart revised 27 Oct 2026',
         fontsize=8, color=muted)
fig.savefig(OUT / 'rural_urban_story_overview.png', dpi=180, facecolor=bg)
fig.savefig(OUT / 'rural_urban_story_overview.svg', facecolor=bg)
plt.close(fig)
notes_path = OUT / 'story_evidence_notes.json'
notes = json.loads(notes_path.read_text(encoding='utf-8'))
notes['editorial_revision_date'] = '2026-10-27'
notes['narrative_order'] = [
    'Plain-language equity concern and definition of the two-map comparison',
    'Observed rural/urban gap in every complete region, with direct regional bars and exact denominators',
    'Discovery-led wildfire deep dive with observed group rates and the adjusted association; full qualifications linked in article_analysis_notes.md',
    'Community deep dives: Porum and Westport, with site visuals',
    'Explicitly hypothetical consequences',
    'Practical response and evidence scope, including adjusted and subgroup limits',
]
notes['lead_chart'] = {
    'file': 'rural_urban_story_overview.png',
    'definition': 'Site-level share with a compatible-category Overture listing within 100 m of OSM geometry',
    'denominators': 'All fire sites in each region and Rural/Urban group; not the one-station-tract subset',
    'excluded': 'One site with unknown rurality; incomplete Texas',
    'limits': 'Descriptive map correspondence, not confirmed omission prevalence or an independent causal rural penalty',
}
notes_path.write_text(json.dumps(notes, indent=2) + '\n', encoding='utf-8')
print(rates.to_json(orient='records', indent=2))
