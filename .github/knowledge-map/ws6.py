"""WS6 integration; read-only site audit, no publishing."""
import json,csv,re,collections,math,itertools,hashlib
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
R=Path('.github/knowledge-map');I=R/'intelligence';O=I/'ws6';O.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(n,rows):
    if not rows:return
    with (O/n).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def clean(s):return re.sub(r'\s+',' ',s).strip()
def safe(r):return 'index' if r=='/' else r.strip('/').replace('/','_').replace('.','_')
docs=[json.loads(x) for x in (R/'content-evidence.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
by={d['url']:d for d in docs};knowledge=[d for d in docs if d['group']!='Tool']
state=load(I/'review-state.json');ws3=load(I/'reviews/ws3-90-pair-mission-triage.json');ws4=load(I/'reviews/ws4-220-relation-decisions.json');ws5=load(I/'reviews/ws5-18-coverage-decisions.json')
assert len(knowledge)==91 and len(ws3['pairs'])==90 and len(ws4['rows'])==220 and len(ws5['flags'])==18
reviews={}
for name in state['review_files']:
    for p in load(I/'reviews'/name)['pages']:
        assert p['url'] not in reviews
        reviews[p['url']]=p
assert len(reviews)==91 and all(reviews[d['url']]['hash']==d['content_sha256'] for d in knowledge)
aliases={a:r for r,d in by.items() for a in (r,'/'+d['file'],r.rstrip('/')+'/')}
hosts={'www.levenshtein.net','levenshtein.net','levenshteinv2.github.io'}
def dest(h,src):
    u=urlsplit(urljoin('https://levenshteinv2.github.io'+src,h))
    return aliases.get(unquote(u.path) or '/') if u.netloc in hosts and u.scheme in ('https','http') else None
def scope(a):
    for n in [a,*a.parents]:
        if not getattr(n,'name',None):continue
        c=set(n.get('class',[]))
        if 'ux-outline' in c:return 'toc'
        if c&{'lv-crumbs','breadcrumb'}:return 'breadcrumb'
        if n.name=='footer':return 'footer'
        if n.name=='header' or c&{'ux-primary','ux-header'}:return 'header'
        if n.name=='aside' or 'lv-aside' in c:return 'sidebar'
        if 'article-body' in c:return 'contextual'
        if 'lv-posts' in c:return 'listing_related'
        if n.name=='nav':return 'navigation'
    return 'main_content' if a.find_parent('main') or a.find_parent('article') or a.find_parent(class_='lv-content') else 'other'
soups={};selflinks=[];allrows=[];risks=[];breadcrumbs=[];ctxrows=[]
for d in knowledge:
    r=d['url'];s=BeautifulSoup(Path(d['file']).read_text(encoding='utf-8'),'html.parser');soups[r]=s
    crumbs=s.select_one('.lv-crumbs, .breadcrumb')
    breadcrumbs.append(dict(url=r,actual_breadcrumb=clean(crumbs.get_text(' ',strip=True)) if crumbs else '',provisional_group=d['group']))
    for a in s.select('a[href]'):
        href=a['href'];t=dest(href,r);sc=scope(a);anchor=clean(a.get_text(' ',strip=True)) or a.get('aria-label','')
        if t is None:continue
        u=urlsplit(urljoin('https://levenshteinv2.github.io'+r,href))
        if t==r:
            if not u.fragment and sc in ('listing_related','contextual','main_content'):
                selflinks.append(dict(url=r,scope=sc,anchor=anchor,href=href))
            continue
        e=dict(source=r,target=t,scope=sc,anchor=anchor,href=href)
        allrows.append(e)
        if sc=='contextual':
            p=a.find_parent(['p','li','td','dd','blockquote']) or a.parent
            e={**e,'context':clean(p.get_text(' ',strip=True))[:900]};ctxrows.append(e)
            if not anchor or anchor.lower() in ('here','click here','read more','more','link'):risks.append({**e,'flag':'generic_or_empty_contextual_anchor'})
            if u.netloc in ('www.levenshtein.net','levenshtein.net'):risks.append({**e,'flag':'absolute_production_host_contextual_link'})
    # Self-links in breadcrumb/current-page menus are intentionally excluded.
csvout('self-links.csv',selflinks);csvout('knowledge-link-occurrences.csv',allrows);csvout('contextual-link-evidence.csv',ctxrows);csvout('risk-flags.csv',risks);csvout('actual-breadcrumbs.csv',breadcrumbs)
pairs={(e['source'],e['target']) for e in allrows};sem={(e['source'],e['target']) for e in allrows if e['scope'] in ('contextual','main_content','listing_related')}
placements=[]
for p in ws4['placement_candidates']:
    r,t=p['source'],p['target'];s=soups[r];area=s.select_one('.article-body') or s.select_one('.lv-content') or s.select_one('main')
    sec=p['section'];anchor=s.find(id=sec) if sec.startswith('ux-section-') else None
    if anchor:
        paras=[]
        for n in anchor.next_siblings:
            if getattr(n,'name',None) in ('h1','h2','h3','h4'):break
            if getattr(n,'name',None):paras.append(clean(n.get_text(' ',strip=True)))
        excerpt=' '.join(paras)[:1800]
    else:excerpt=clean(area.get_text(' ',strip=True))[:1800] if area else ''
    placements.append({**p,'source_exists':r in soups,'target_exists':t in by,'section_id_exists':bool(anchor) if sec.startswith('ux-section-') else None,'already_content_link':(r,t) in sem,'source_excerpt':excerpt,'status':'placement_evidence_extracted_pending_sentence_review'})
assert len(placements)==18
assert all(p['source_exists'] and p['target_exists'] and p['section_id_exists'] is not False for p in placements)
save('placement-evidence.json',placements)
# Section-level candidate comparison using local TF-IDF; ranks possible repetition, not deletion decisions.
profiles={d['url']:load(I/'profiles'/(safe(d['url'])+'.json')) for d in knowledge}
stop=set('the a an of to in on for is are was were be with and or as by from that this these those it its can may not at if then than which what how when where why used using each more most other between both their they into about does do has have been will would should one two'.split())
def toks(t):return [w for w in re.findall(r'[a-z][a-z0-9]+',t.lower()) if w not in stop]
def sections(p):
    out=[]
    for s in p['sections']:
        body=' '.join(s['paragraphs']);ts=toks(body)
        if len(ts)>=12 and not re.search(r'references|related.*resources|related posts',s['heading'],re.I):
            out.append((s,collections.Counter(ts),body))
    return out
overlap=[]
for pair in ws3['pairs']:
    if pair['category'] not in ('section_overlap_review','hierarchy_review'):continue
    a,b=pair['a'],pair['b'];aa=sections(profiles[a]);bb=sections(profiles[b]);allsec=aa+bb
    df=collections.Counter(w for s,c,t in allsec for w in c)
    def vector(c):
        v={w:(1+math.log(n))*math.log((len(allsec)+1)/(df[w]+1)) for w,n in c.items()}
        norm=math.sqrt(sum(n*n for n in v.values())) or 1
        return {w:n/norm for w,n in v.items()}
    av=[vector(c) for s,c,t in aa];bv=[vector(c) for s,c,t in bb]
    best=[]
    for i,j in itertools.product(range(len(aa)),range(len(bb))):
        x,y=av[i],bv[j];score=sum(x[w]*y[w] for w in x.keys()&y.keys())
        if score>=.20:best.append((score,i,j))
    best.sort(reverse=True)
    matches=[]
    for sc,i,j in best[:8]:
        sa,_,ta=aa[i];sb,_,tb=bb[j]
        matches.append(dict(score=round(sc,4),a_section=sa['heading'],a_id=sa['id'],a_excerpt=ta[:1000],b_section=sb['heading'],b_id=sb['id'],b_excerpt=tb[:1000]))
    overlap.append(dict(rank=pair['rank'],a=a,b=b,category=pair['category'],mission_decision=pair['decision'],section_counts=[len(aa),len(bb)],matches=matches,status='section_evidence_pending_editorial_decision'))
assert len(overlap)==25
save('section-overlap-evidence.json',overlap)
# A graph export is explicit about actual and proposed relationships. No invented links.
with (R/'internal-link-occurrences.csv').open(encoding='utf-8-sig',newline='') as f:original=list(csv.DictReader(f))
graph={}
for e in original:
    k=(e['source'],e['target']);v=graph.setdefault(k,dict(source=k[0],target=k[1],actual_scopes=set(),proposed=False,proposed_relation='',decision='retain_unless_reviewed'));v['actual_scopes'].add(e['scope'])
for e in placements:
    k=(e['source'],e['target']);v=graph.setdefault(k,dict(source=k[0],target=k[1],actual_scopes=set(),proposed=False,proposed_relation='',decision=''));v.update(proposed=True,proposed_relation=e['kind'],decision='candidate_pending_qa')
csvout('full-target-graph.csv',[{**v,'actual_scopes':' | '.join(sorted(v['actual_scopes']))} for v in graph.values()])
# corrected taxonomy, primary structure distinct from semantic associations.
correct={'/indexing-and-filtering-for-edit-distance':'Algorithms','/spell-and-query-correction':'Search'}
registry=[]
for d in knowledge:
    r=d['url'];p=reviews[r];registry.append(dict(url=r,group=correct.get(r,d['group']),entity=p['primary_entity'],mission=p['mission'],intent=p['intent_hypothesis'],boundary=p['boundary'],supporting_entities=p['supporting_entities'],hash=d['content_sha256'],status='mission_reviewed_full_semantic_pending'))
save('target-knowledge-registry.json',registry)
counts=collections.Counter(e['scope'] for e in selflinks);rf=collections.Counter(e['flag'] for e in risks)
summary=dict(snapshot=state['snapshot'],coverage_gate='PASS',knowledge_pages=len(knowledge),reviewed_missions=len(registry),overlap_pairs=90,section_evidence_pairs=len(overlap),relationship_rows=220,coverage_flags=18,placement_candidates=len(placements),placement_sections_found=sum(p['section_id_exists'] is True for p in placements),placement_already_content=sum(p['already_content_link'] for p in placements),bibliography_candidates=len(ws5['reference_url_candidates']),knowledge_link_occurrences=len(allrows),knowledge_link_pairs=len(pairs),contextual_occurrences=len(ctxrows),contextual_pairs=len({(e['source'],e['target']) for e in ctxrows}),self_link_occurrences=len(selflinks),self_link_pages=len({e['url'] for e in selflinks}),self_link_scopes=dict(counts),self_related_pages=len({e['url'] for e in selflinks if e['scope']=='listing_related'}),risk_flags=dict(rf),target_graph_pairs=len(graph),new_graph_pairs=sum(not v['actual_scopes'] for v in graph.values()),semantic_gate='PENDING_EDITORIAL_AND_SOURCE_QA',site_changes=0)
save('summary.json',summary)
print('WS6 SUMMARY',json.dumps(summary,ensure_ascii=False))
print('WS6 OVERLAP',json.dumps([dict(rank=p['rank'],a=p['a'],b=p['b'],best=p['matches'][:2]) for p in overlap],ensure_ascii=False))
