from run_discovery import *
from shapely.geometry import shape,box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon
from matplotlib.collections import PatchCollection,LineCollection
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
BG='#f8f6ef';INK='#18352e';RURAL='#ba4b2f';URBAN='#15786e';ROAD='#c6b992';BUILD='#d8ddd6'
E=json.loads((OUT/'named_case_evidence.json').read_text())
sites=json.loads((CACHE/'eastern-ok.sites.geojson').read_text())['features']
layers={name:json.loads((ROOT/'work'/f'eastern-ok_{name}_map.geojson').read_text())['features'] for name in ['buildings','roads']}
pois=pq.read_table(DATA/'eastern-ok-overture-pois.parquet',columns=['id','names','categories','geometry']).to_pylist()
fire=[]
for p in pois:
    cats=p.get('categories') or {}
    if set([cats.get('primary')]+(cats.get('alternate') or []))&TYPES['fire']:
        p['geom']=from_wkb(p.pop('geometry'));fire.append(p)
porum=E['porum']['osm'];control=next(s for s in sites if s['properties']['GEOID']=='40111000300' and s['properties']['facility_type']=='fire')
def window(feature):
    p=feature['properties'];dx=.0045/math.cos(math.radians(p['lat']));return p['lon']-dx,p['lat']-.0045,p['lon']+dx,p['lat']+.0045
def draw_geom(ax,g,**kw):
    if g.geom_type=='Polygon':ax.add_patch(PatchPolygon(np.asarray(g.exterior.coords),**kw))
    elif g.geom_type=='MultiPolygon':
        for sub in g.geoms:draw_geom(ax,sub,**kw)
def panel(ax,feature,title,overlay):
    w,s,e,n=window(feature);clip=box(w,s,e,n);ax.set_facecolor(BG)
    for f in layers['buildings']:
        g=shape(f['geometry'])
        if g.intersects(clip):draw_geom(ax,g,facecolor=BUILD,edgecolor='#afb8ad',linewidth=.25)
    for f in layers['roads']:
        g=shape(f['geometry'])
        if g.intersects(clip):
            for line in list(g.geoms) if g.geom_type=='MultiLineString' else [g]:
                if line.geom_type=='LineString':ax.plot(*line.xy,color=ROAD,lw=1.2,zorder=1)
    if overlay=='osm':
        draw_geom(ax,shape(feature['geometry']),facecolor=RURAL,edgecolor=RURAL,alpha=.75,zorder=5)
        p=feature['properties'];ax.scatter([p['lon']],[p['lat']],s=85,c=RURAL,marker='^',edgecolor='white',zorder=6)
        ax.annotate('Volunteer fire station\nOSM identifies the function',(p['lon'],p['lat']),xytext=(20,35),textcoords='offset points',fontsize=10,color=INK,arrowprops={'arrowstyle':'-','color':RURAL},bbox={'boxstyle':'round,pad=.4','fc':'white','ec':'none'},zorder=9)
    else:
        for p in fire:
            g=p['geom']
            if clip.covers(g):
                ax.scatter([g.x],[g.y],s=75,c=URBAN,marker='^',edgecolor='white',zorder=6)
                ax.annotate((p.get('names') or {}).get('primary','Fire place'),(g.x,g.y),xytext=(15,25),textcoords='offset points',color=URBAN,fontsize=9,bbox={'boxstyle':'round,pad=.3','fc':'white','ec':'none'},zorder=9)
        if overlay=='empty':
            p=feature['properties'];draw_geom(ax,shape(feature['geometry']),facecolor='none',edgecolor=RURAL,lw=1.5,zorder=5)
            ax.annotate('Building footprint present\nNo nearby fire-category place',(p['lon'],p['lat']),xytext=(20,35),textcoords='offset points',fontsize=10,color=INK,arrowprops={'arrowstyle':'-','color':RURAL},bbox={'boxstyle':'round,pad=.4','fc':'white','ec':'none'},zorder=9)
    scale=.002/math.cos(math.radians((s+n)/2));x=w+(e-w)*.07;y=s+(n-s)*.08
    ax.plot([x,x+scale],[y,y],color=INK,lw=3);ax.text(x+scale/2,y+(n-s)*.025,'~220 m',ha='center',fontsize=9,color=INK)
    ax.text(e-(e-w)*.06,n-(n-s)*.08,'N ↑',ha='right',color=INK,fontsize=9)
    ax.set_xlim(w,e);ax.set_ylim(s,n);ax.set_aspect(1/math.cos(math.radians((s+n)/2)));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(title,loc='left',fontsize=12,color=INK,pad=10)
    for spine in ax.spines.values():spine.set_color('#d9d9cf')
fig,axs=plt.subplots(1,3,figsize=(15,5.6));fig.patch.set_facecolor(BG)
panel(axs[0],porum,'A  Porum · Overture places','empty');panel(axs[1],porum,'B  Same location · OSM identity','osm');panel(axs[2],control,'C  Urban contrast · Okmulgee','overture')
fig.suptitle('The building is mapped. The fire-station identity is elsewhere.',x=.05,ha='left',fontsize=19,fontweight='bold',color=INK)
fig.text(.05,.12,'Equal map scale: ~1 km × 1 km. Panels A–B share the same Overture buildings and roads; only the facility overlay changes.',fontsize=10,color=INK)
fig.text(.05,.075,'Porum tract 40101001502: 2,189 people, 1 OSM fire site. Urban tract 40111000300: 2,738 people, 1 OSM fire site. Illustrative pair.',fontsize=9,color=INK)
fig.text(.05,.035,'Sources: challenge Overture 2026-08-19.0; © OpenStreetMap contributors, historical state 2026-08-01 (ODbL). Retrieved 24 Oct 2026.',fontsize=8,color=INK)
fig.subplots_adjust(left=.05,right=.98,top=.82,bottom=.19,wspace=.12);fig.savefig(OUT/'same_site_comparison.png',dpi=180,facecolor=BG);plt.close(fig)
# Straight-line coordinate discrepancy; avoid implying a routing calculation.
fig,ax=plt.subplots(figsize=(8,5));fig.patch.set_facecolor(BG);ax.set_facecolor(BG)
p=porum['properties'];g=shape(E['porum']['overture']['geometry'])
ax.plot([p['lon'],g.x],[p['lat'],g.y],color=RURAL,lw=2,ls='--');ax.scatter([p['lon'],g.x],[p['lat'],g.y],s=[100,100],c=[RURAL,URBAN])
ax.annotate('OSM station site · Porum\nRural tract 40101001502',(p['lon'],p['lat']),xytext=(12,-15),textcoords='offset points',fontsize=9)
ax.annotate('Same-name Overture place\nMuskogee · tract 40101000400',(g.x,g.y),xytext=(12,-5),textcoords='offset points',fontsize=9)
ax.text(1.05,.48,'44.4 km',transform=ax.transAxes,fontsize=25,color=RURAL,fontweight='bold',bbox={'fc':BG,'ec':'none'})
ax.set_xlim(p['lon']-.13,g.x+.19);ax.set_ylim(p['lat']-.09,g.y+.08);ax.set_aspect(1/math.cos(math.radians(p['lat'])));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.grid(color='#e1dfd2',lw=.6)
fig.suptitle('A facility count can hide a location error',x=.06,ha='left',fontsize=17,color=INK,y=.96)
fig.text(.1,.035,'Approximate straight-line separation, not travel distance. Same street number; different locality and postcode.',fontsize=8,color=INK)
ax.set_position([.1,.19,.48,.63]);fig.savefig(OUT/'porum_location_discrepancy.png',dpi=180,facecolor=BG);plt.close(fig)
# Regional fire correspondence, with sensitivity range (not confidence intervals).
allrows=[]
for r in REGIONS:
    path=OUT/f'{r}_facility_audit.csv'
    if path.exists():allrows.append(pd.read_csv(path,dtype={'GEOID':str}))
d=pd.concat(allrows);d=d[d.facility_type=='fire'];regions=[r for r in REGIONS if r in set(d.region)]
labels={'eastern-ok':'Eastern Oklahoma','eastern-wa':'Eastern Washington','maricopa-az':'Maricopa + surrounding','northern-ca':'Northern California','south-central-tx':'South-Central Texas'}
fig,ax=plt.subplots(figsize=(10,max(4,1+len(regions)*.9)));fig.patch.set_facecolor(BG);ax.set_facecolor(BG)
for i,r in enumerate(regions):
    for group,dy,col in [('Rural',-.13,RURAL),('Urban',.13,URBAN)]:
        f=d[(d.region==r)&(d.ur_class==group)]
        if not len(f):continue
        rate=f.compatible_100m.mean()*100;lo=f.compatible_50m.mean()*100;hi=f.compatible_200m.mean()*100
        ax.plot([lo,hi],[i+dy]*2,color=col,lw=3,alpha=.5);ax.scatter([rate],[i+dy],s=65,color=col,label=group if i==0 else None,zorder=3)
        ax.text(hi+2,i+dy,f'{rate:.0f}%  (n={len(f)})',va='center',fontsize=10,color=col)
ax.set_yticks(range(len(regions)),[labels[r] for r in regions]);ax.invert_yaxis();ax.set_xlim(0,112);ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('OSM fire sites with a compatible Overture place nearby (%)');ax.grid(axis='x',alpha=.2);ax.legend(loc='lower right',frameon=False)
ax.set_title('Does the rural correspondence gap recur?',loc='left',fontsize=18,fontweight='bold',pad=23,color=INK)
fig.text(.03,.025,'Dots: 100 m from OSM site geometry. Lines: sensitivity at 50–200 m; these are not confidence intervals. OSM is an incomplete comparator.',fontsize=8,color=INK)
fig.tight_layout(rect=(0,.07,1,1));fig.savefig(OUT/'regional_fire_comparison.png',dpi=180,facecolor=BG);plt.close(fig)
# Physical checks, separated from assumptions about a building's function.
checks={}
for label,feat in [('porum',porum),('urban_control',control)]:
    g=shape(feat['geometry']);lat=feat['properties']['lat'];point=Point(feat['properties']['lon'],lat)
    bs=[(f,shape(f['geometry'])) for f in layers['buildings']]
    overlaps=[f for f,b in bs if b.intersects(g)]
    checks[label]={'intersecting_overture_buildings':len(overlaps),'overture_buildings':overlaps,'nearest_road_m':min(distance(g,shape(f['geometry']),lat) for f in layers['roads']),'point_inside_overture_building':any(b.covers(point) for f,b in bs)}
(OUT/'physical_site_checks.json').write_text(json.dumps(checks,indent=2))
print('FIGURES SAVED', {k:{m:v for m,v in x.items() if m!='overture_buildings'} for k,x in checks.items()},flush=True)
