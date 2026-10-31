from run_discovery import *
from concurrent.futures import ThreadPoolExecutor
dest=ROOT/'work/review_sources';dest.mkdir(exist_ok=True)
def address():
    url='https://services8.arcgis.com/vVsGmpWOxUEQGPFl/arcgis/rest/services/Address_Points_033021/FeatureServer/0/query?'+urllib.parse.urlencode({'f':'json','where':"SITUS_NUMB = '37551' OR HOUSENUM = '37551'",'outFields':'SITUS_ALL,SITUS_NUMB,SITUS_ROAD,COMMUNITY,HOUSENUM,STREET','outSR':'4326','returnGeometry':'true'})
    path=dest/'westport_official_address_query.json'
    if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
    print('WESTPORT ADDRESS',path.read_text(),flush=True)
def contract():
    path=dest/'porum_official_contract.pdf'
    if not path.exists():
        url='https://muskogee.okcounties.org/file/item_8_-_contract_porum_vfd_fire_master_fire_equipment_2427.pdf'
        path.write_bytes(urllib.request.urlopen(url,timeout=90).read())
    from pypdf import PdfReader
    reader=PdfReader(path);hits=[]
    for i,p in enumerate(reader.pages):
        txt=p.extract_text() or ''
        if re.search(r'205|Porum',txt,re.I):hits.append({'page':i+1,'text':txt})
    (dest/'porum_contract_text_hits.json').write_text(json.dumps(hits,indent=2))
    print('CONTRACT',len(reader.pages),'pages',path.stat().st_size,'bytes','hits',[(x['page'],x['text'][:1200]) for x in hits[:8]],flush=True)
with ThreadPoolExecutor(max_workers=2) as pool:
    for f in [pool.submit(address),pool.submit(contract)]:
        try:f.result()
        except Exception as e:print(type(e).__name__,str(e),flush=True)
