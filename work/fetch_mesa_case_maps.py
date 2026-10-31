from fetch_map_layers import *
from shapely.geometry import shape
c=next(c for c in json.loads((ROOT/'work/recurrence_candidates.json').read_text()) if c['region']=='maricopa-az')
windows=[]
for geometry in [c['osm']['geometry'],c['overture']['geometry']]:
    p=shape(geometry).representative_point();dy=.0018;dx=dy/math.cos(math.radians(p.y));windows.append([p.x-dx,p.y-dy,p.x+dx,p.y+dy])
layers={x['layer']:x for x in fetch_layers('maricopa-az',windows,tag='_mesa')}
checks={'name':c['name'],'region':c['region'],'distance_km':c['distance_km'],'same_tract':c['same_tract'],'sites':{}}
for label,geometry in [('osm',c['osm']['geometry']),('overture',c['overture']['geometry'])]:
    g=shape(geometry);p=g.representative_point();b=[f for f in layers['buildings']['features'] if shape(f['geometry']).intersects(g)]
    checks['sites'][label]={'overlapping_buildings':len(b),'point_inside_building':any(shape(f['geometry']).covers(p) for f in b),'nearest_road_m':min(distance(g,shape(f['geometry']),p.y) for f in layers['roads']['features']),'building_ids':[f['properties']['id'] for f in b]}
allchecks=json.loads((OUT/'all_ten_physical_site_checks.json').read_text())+[checks]
(OUT/'reviewed_case_physical_checks.json').write_text(json.dumps(allchecks,indent=2));print(checks,flush=True)
