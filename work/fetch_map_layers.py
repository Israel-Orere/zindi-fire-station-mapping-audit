"""Fetch only intersecting row groups of permitted Overture map layers."""
from run_discovery import *
import io
class RemoteFile(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0;self.bytes=0
        req=urllib.request.Request(url,method='HEAD')
        with urllib.request.urlopen(req,timeout=60) as r:self.size=int(r.headers['Content-Length'])
        self.cache=ROOT/'work/map_ranges';self.cache.mkdir(exist_ok=True)
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,off,whence=0):
        self.pos=off if whence==0 else self.pos+off if whence==1 else self.size+off
        return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        n=min(n,self.size-self.pos)
        if n<=0:return b''
        key=hashlib.sha256(f'{self.url}:{self.pos}:{n}'.encode()).hexdigest();p=self.cache/(key+'.bin')
        if p.exists():raw=p.read_bytes()
        else:
            req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'})
            with urllib.request.urlopen(req,timeout=90) as r:
                if r.status!=206:raise RuntimeError('Server did not honor range; refusing full download')
                raw=r.read()
            if len(raw)!=n:raise ValueError('Incomplete range response')
            p.write_bytes(raw);self.bytes+=len(raw)
        self.pos+=len(raw);return raw
def fetch_layers(region,windows,tag=''):
    layers=[]
    for layer in ['buildings','roads']:
        out=ROOT/'work'/f'{region}{tag}_{layer}_map.geojson'
        if out.exists():layers.append(json.loads(out.read_text()));continue
        url=f'https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/reference/{region}/{region}-overture-{layer}.parquet'
        remote=RemoteFile(url);p=pq.ParquetFile(remote)
        names=p.schema_arrow.names;cols=[c for c in ['id','names','sources','class','geometry','bbox'] if c in names]
        from shapely.geometry import box
        ws=[box(*b) for b in windows];features=[]
        for i in range(p.num_row_groups):
            rg=p.metadata.row_group(i);stats={}
            for j in range(rg.num_columns):
                col=rg.column(j)
                if col.path_in_schema.startswith('bbox.') and col.statistics:stats[col.path_in_schema.split('.')[1]]=col.statistics
            intersects=not stats or any(stats['xmin'].min<=e and stats['xmax'].max>=w and stats['ymin'].min<=n and stats['ymax'].max>=s for w,s,e,n in windows)
            if not intersects:continue
            print('map rowgroup',region,layer,i,flush=True)
            for r in p.read_row_group(i,columns=cols).to_pylist():
                b=r['bbox']
                if not any(b['xmin']<=e and b['xmax']>=w and b['ymin']<=n and b['ymax']>=s for w,s,e,n in windows):continue
                g=from_wkb(r.pop('geometry'));r.pop('bbox',None)
                if any(g.intersects(win) for win in ws):features.append({'type':'Feature','properties':r,'geometry':g.__geo_interface__})
        obj={'type':'FeatureCollection','layer':layer,'source_url':url,'windows':windows,'bytes_fetched':remote.bytes,'features':features}
        out.write_text(json.dumps(obj));layers.append(obj)
        print('map complete',region,layer,len(features),remote.bytes,flush=True)
    return layers
if __name__=='__main__':
    config=json.loads((ROOT/'work/map_windows.json').read_text())
    for region,windows in config.items():fetch_layers(region,windows)
