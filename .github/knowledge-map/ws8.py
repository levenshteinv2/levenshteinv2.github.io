import json, re, csv, hashlib, subprocess, urllib.request, urllib.parse, concurrent.futures
from collections import Counter, defaultdict
from pathlib import Path
from bs4 import BeautifulSoup
BASE='57cd23dc4aad16c7ab69d99e9fa5c98aadcb71b7'
HOST='www.levenshtein.net'
ORIGIN='https://'+HOST
OUT=Path('.github/knowledge-map/intelligence/ws8')
OUT.mkdir(parents=True,exist_ok=True)
def git(*args):
    return subprocess.check_output(['git',*args])
manifest=json.loads(git('show',BASE+':.github/qa/pages.json'))
assert len(manifest)==len(set(manifest))==91
tools='fancy-text-generator schriftgenerator generador-de-letras letras-diferentes font-henkan krasivyy-shrift ki-tu-dac-biet letras-bonitas yazi-stilleri font-style te-shu-zi-ti caratteri-speciali akson-phiset font-aesthetic lettertypes police-d-ecriture generator-czcionek'.split()
tree=set(git('ls-tree','-r','--name-only',BASE).decode().splitlines())
def route(p):
    return '/' if p=='index.html' else '/'+p.removesuffix('.html')
def dump(p,data):
    (OUT/p).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p,items,fields):
    with (OUT/p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(items)
def normurl(v):
    if not isinstance(v,str):return ''
    u=urllib.parse.urlsplit(v)
    if u.netloc and u.netloc.lower() not in (HOST,'levenshtein.net','levenshteinv2.github.io'):return v
    if not u.path and not u.netloc:return v
    p=u.path or '/'
    if p.endswith('/index.html'):p=p[:-10]
    if p.endswith('.html'):p=p[:-5]
    return p.rstrip('/') or '/'
def text(x):
    return ' '.join(str(x or '').split())
def serialized(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def types(n):
    t=n.get('@type',[])
    return [t] if isinstance(t,str) else t if isinstance(t,list) else []
def walk(x,path='$'):
    if isinstance(x,dict):
        yield x,path
        for k,v in x.items():
            if k!='@context':yield from walk(v,path+'.'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x):yield from walk(v,path+'['+str(i)+']')
def meta(s,k):
    t=s.find('meta',attrs={'name':k}) or s.find('meta',attrs={'property':k})
    return t.get('content','') if t else ''
def load_tool(slug):
    r='/'+slug
    for p in [slug+'.html',slug+'/index.html',slug]:
        if p in tree:return (r,p,'preview_snapshot',git('show',BASE+':'+p).decode('utf-8'),None)
    # Read-only public source. Never treat HTTP 200 alone as correct identity.
    try:
        req=urllib.request.Request(ORIGIN+r,headers={'User-Agent':'Mozilla/5.0 (compatible; LevenshteinSchemaAudit/1.0)'})
        with urllib.request.urlopen(req,timeout=15) as res:
            final=res.geturl();body=res.read(8_000_000).decode('utf-8','replace')
        s=BeautifulSoup(body,'html.parser');can=s.select_one('link[rel=canonical]')
        if normurl(final)!=r or not can or normurl(can.get('href'))!=r or not s.h1:
            return (r,None,'production_unverified',None,{'final':final,'canonical':can.get('href') if can else None,'reason':'route/canonical/h1 gate'})
        return (r,None,'production_readonly',body,{'final':final,'canonical':can.get('href'),'h1':text(s.h1.get_text(' ',strip=True))})
    except Exception as e:return (r,None,'production_unavailable',None,{'error':str(e)})
items=[(route(p),p,'preview_snapshot',git('show',BASE+':'+p).decode('utf-8'),None) for p in manifest]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:items+=list(ex.map(load_tool,tools))
pages=[];defs=defaultdict(list);refs=[];external=[];risks=[];nodes=[];owner_nodes=defaultdict(list);typ=Counter();issues=Counter()
def flag(r,code,detail):
    risks.append(dict(route=r,code=code,detail=detail));issues[code]+=1
for r,p,src,body,access in items:
    row=dict(route=r,path=p,source=src,tool=r.lstrip('/') in tools,access=access)
    if body is None:
        row.update(status='NOT_INSPECTED',script_count=0)
        pages.append(row);continue
    s=BeautifulSoup(body,'html.parser')
    can=s.select_one('link[rel=canonical]')
    canonical=can.get('href','') if can else ''
    title=text(s.title.get_text(' ',strip=True)) if s.title else ''
    desc=meta(s,'description')
    main=s.select_one('main') or s.body or s
    visible=set(normurl(a.get('href','')) for a in main.select('a[href]'))
    h1=[text(x.get_text(' ',strip=True)) for x in s.select('h1')]
    scripts=s.select('script[type="application/ld+json"]')
    row.update(status='INSPECTED',sha256=hashlib.sha256(body.encode()).hexdigest(),canonical=canonical,title=title,description=desc,h1=h1,lang=s.html.get('lang','') if s.html else '',robots=meta(s,'robots'),script_count=len(scripts),parse_errors=0,top_types=[],own_nodes=[],schema_nodes=0)
    if not scripts:flag(r,'no_jsonld_optional','No JSON-LD; not automatically an error')
    if normurl(canonical)!=r:flag(r,'canonical_route_mismatch',canonical)
    for si,tag in enumerate(scripts):
        try:doc=json.loads(tag.string or tag.get_text())
        except Exception as e:
            row['parse_errors']+=1;flag(r,'invalid_jsonld',str(e));continue
        top=doc.get('@graph',[doc]) if isinstance(doc,dict) else doc if isinstance(doc,list) else []
        for g in top:
            if isinstance(g,dict):row['top_types']+=types(g)
        for n,jpath in walk(doc):
            ident=n.get('@id');ts=types(n)
            if ts:
                typ.update(ts);row['schema_nodes']+=1
                nodes.append(dict(route=r,source=src,jsonpath=jpath,id=ident,types=ts,data=n))
            if isinstance(ident,str):
                if len(set(n)-{'@id','@context'})>0:
                    defs[ident].append(dict(route=r,source=src,jsonpath=jpath,data=n))
                else:refs.append(dict(route=r,source=src,jsonpath=jpath,id=ident))
            own=bool(ident and isinstance(ident,str) and ident.startswith(ORIGIN) and normurl(ident)==r)
            if own and ts:
                row['own_nodes'].append(dict(id=ident,types=ts,name=n.get('name') or n.get('headline'),mainEntity=n.get('mainEntity')))
                owner_nodes[ident].append(dict(route=r,data=n))
                if any(t in ('WebPage','CollectionPage','AboutPage','TechArticle','Article','BlogPosting','FAQPage','SoftwareApplication','WebApplication') for t in ts):
                    sd=n.get('description')
                    if isinstance(sd,str) and desc and text(sd)!=text(desc):
                        flag(r,'page_description_diff_review',ident)
                    if isinstance(n.get('url'),str) and normurl(n['url'])!=r:
                        flag(r,'own_node_url_mismatch',ident)
                    if n.get('inLanguage') and isinstance(n['inLanguage'],str) and row['lang'] and n['inLanguage'].split('-')[0]!=row['lang'].split('-')[0]:
                        flag(r,'language_mismatch',ident)
                if 'TechArticle' in ts or 'Article' in ts:
                    for key in ['datePublished','dateModified']:
                        d=n.get(key)
                        if d:row.setdefault('article_dates',[]).append(dict(id=ident,field=key,value=d,visible_date_candidate=str(d)[:10] in main.get_text(' ',strip=True) or bool(main.select('time[datetime^="'+str(d)[:10]+'"]'))))
                    for key in ['author','publisher']:
                        a=n.get(key)
                        if isinstance(a,dict) and not a.get('@id'):flag(r,'unidentified_'+key,serialized(a))
                if 'ItemList' in ts or 'BreadcrumbList' in ts:
                    elements=n.get('itemListElement',[])
                    if isinstance(elements,list):
                        positions=[x.get('position') for x in elements if isinstance(x,dict)]
                        if positions and positions!=list(range(1,len(positions)+1)):flag(r,'list_positions_review',ident)
                        for x in elements:
                            if not isinstance(x,dict):continue
                            a=x.get('item') or x.get('url')
                            target=a.get('@id') or a.get('url') if isinstance(a,dict) else a
                            if isinstance(target,str) and target.startswith(ORIGIN) and normurl(target) not in visible|{r,'/'}:
                                flag(r,'list_target_not_in_main_review',str(target))
            for key in ['sameAs','citation']:
                if key not in n:continue
                values=n[key] if isinstance(n[key],list) else [n[key]]
                for v in values:
                    target=v.get('@id') or v.get('url') if isinstance(v,dict) else v
                    if isinstance(target,str):external.append(dict(route=r,node=ident or '',property=key,target=target,visible_link_exact=bool(s.find('a',href=target))))
    if scripts and not row['own_nodes']:flag(r,'no_own_typed_id_review','No typed node ID matching page canonical route')
    pages.append(row)
# Repeated scalar assertions are candidates, not proven contradiction. Names and descriptions may be complementary.
conflicts=[];registry=[]
for ident,occ in sorted(defs.items()):
    vals=defaultdict(lambda:defaultdict(set))
    for o in occ:
        for k in ('@type','name','description','headline','url','inLanguage','datePublished','dateModified'):
            if k in o['data']:vals[k][serialized(o['data'][k])].add(o['route'])
    for k,v in vals.items():
        if len(v)>1:conflicts.append(dict(id=ident,property=k,values=[dict(value=json.loads(x),routes=sorted(y)) for x,y in sorted(v.items())],status='REVIEW_NOT_AUTOMATIC_CONTRADICTION'))
    registry.append(dict(id=ident,definitions=len(occ),pages=sorted(set(o['route'] for o in occ)),owner_candidates=sorted(set(o['route'] for o in owner_nodes.get(ident,[]))),types=sorted(set(t for o in occ for t in types(o['data']))),name_candidates=sorted(set(text(o['data'].get('name') or o['data'].get('headline')) for o in occ)-{''})))
internal_refs=[x for x in refs if x['id'].startswith(ORIGIN)]
unresolved=[x for x in internal_refs if x['id'] not in defs]
for x in unresolved:flag(x['route'],'unresolved_internal_id_review',x['id'])
known=[p for p in pages if not p['tool']]
toolpages=[p for p in pages if p['tool']]
summary=dict(snapshot=BASE,knowledge_pages=len(known),knowledge_inspected=sum(p['status']=='INSPECTED' for p in known),tool_nodes=len(toolpages),tools_preview=sum(p['source']=='preview_snapshot' for p in toolpages),tools_production_readonly=sum(p['source']=='production_readonly' for p in toolpages),tools_uninspected=sum(p['status']!='INSPECTED' for p in toolpages),jsonld_knowledge_pages=sum(p['script_count']>0 for p in known),jsonld_tool_pages=sum(p['script_count']>0 for p in toolpages),json_parse_errors=sum(p.get('parse_errors',0) for p in pages),typed_nodes=sum(typ.values()),type_counts=dict(typ),distinct_ids=len(defs),internal_reference_occurrences=len(internal_refs),unresolved_internal_reference_occurrences=len(unresolved),scalar_variant_groups=len(conflicts),scalar_variant_ids=len(set(x['id'] for x in conflicts)),external_reference_occurrences=len(external),unique_external_targets=len(set(x['target'] for x in external)),risk_counts=dict(issues),scope='Pinned Preview source plus read-only public fallback for absent tools; no production or tool edits',machine_gate='PASS' if len(known)==91 and all(p['status']=='INSPECTED' for p in known) and not any(p.get('parse_errors') for p in known) else 'FAIL',semantic_gate='PENDING',google_rich_results='NOT_RUN',schema_org_vocabulary_validation='NOT_RUN',site_changes=0)
dump('summary.json',summary);dump('page-inventory.json',pages);dump('entity-registry.json',registry);dump('scalar-variants.json',conflicts);dump('typed-node-evidence.json',nodes);dump('unresolved-internal-refs.json',unresolved);dump('external-reference-queue.json',external);dump('review-queue.json',risks)
print(json.dumps(summary,ensure_ascii=False))
assert summary['machine_gate']=='PASS'
