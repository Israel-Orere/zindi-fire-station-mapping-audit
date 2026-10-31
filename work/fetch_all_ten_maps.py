from fetch_map_layers import *
from shapely.geometry import shape
cases=json.loads((ROOT/'work/original_ten_cases.json').read_text())
allchecks=[]
for region in sorted(set(c['region'] for c in cases)):
    selected=[c for c in cases if c['region']==region];windows=[]
    for c in selected:
        for geometry in [c['osm']['geometry'],c['overture']['geometry']]:
            g=shape(geometry);p=g.representative_point();dy=.0018;dx=dy/math.cos(math.radians(p.y));windows.append([p.x-dx,p.y-dy,p.x+dx,p.y+dy])
    layers={x['layer']:x for x in fetch_layers(region,windows,tag='_all_ten')}
    for c in selected:
        checks={'name':c['name'],'region':region,'distance_km':c['distance_km'],'same_tract':c['same_tract'],'sites':{}}
        for label,geometry in [('osm',c['osm']['geometry']),('overture',c['overture']['geometry'])]:
            g=shape(geometry);p=g.representative_point();b=[f for f in layers['buildings']['features'] if shape(f['geometry']).intersects(g)]
            checks['sites'][label]={'overlapping_buildings':len(b),'point_inside_building':any(shape(f['geometry']).covers(p) for f in b),'nearest_road_m':min(distance(g,shape(f['geometry']),p.y) for f in layers['roads']['features']),'building_ids':[f['properties']['id'] for f in b]}
        allchecks.append(checks)
        print('checked',c['name'],checks['sites'],flush=True)
    (OUT/'all_ten_physical_site_checks.json').write_text(json.dumps(allchecks,indent=2))
