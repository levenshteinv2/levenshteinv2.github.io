"""Reproducible evidence extraction and candidate generation. No LLM/API; no site mutation."""
import csv,json,re,math,collections,hashlib,itertools
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
ROOT=Path('.github/knowledge-map')
OUT=ROOT/'intelligence';OUT.mkdir(exist_ok=True)
P=OUT/'profiles';P.mkdir(exist_ok=True)
docs=[json.loads(x) for x in (ROOT/'content-evidence.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
knowledge=[d for d in docs if d['group']!='Tool']
assert len(knowledge)==91 and len(docs)==108 and len({d['url'] for d in docs})==108
assert all(d['source']=='preview_repo' and d.get('body') for d in knowledge)
by={d['url']:d for d in docs}
def readcsv(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
links=readcsv('internal-link-occurrences.csv')
proposals=readcsv('proposed-entity-links.csv')
def save(name,o):
    (OUT/name).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def csvout(name,rows):
    if not rows:return
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def clean(s):return re.sub(r'\s+',' ',s).strip()
def label(d):return d['h1'][0] if d.get('h1') else d.get('title','') or d['url']
def words(s):return re.findall(r"[a-z][a-z0-9]+",s.lower())
stop=set("the a an and or of to in on for is are be with as by from that this these those it its can may also not at if than then which what how when where why use used using each such more most other between both their they into about does do has have been will would should one two first second based example cases case algorithm algorithms distance edit levenshtein string strings".split())
def tokens(s):return [x for x in words(s) if x not in stop and len(x)>2]
def safe(r):return 'index' if r=='/' else r.strip('/').replace('/','_').replace('.','_')
def norm(s):return clean(re.sub(r'[^a-z0-9]+',' ',s.lower()))
def name_alias(d):
    r=d['url']
    if r=='/':return ['Levenshtein distance','Levenshtein algorithm']
    if d['group'] in ('Legacy','Tool'):return []
    # Explicit entity labels from page titles and canonical slug; no unsupported NER assertions.
    h=label(d).split(':')[0].split('|')[0]
    slug=r.strip('/').replace('-',' ')
    names=[h,slug]
    return list(dict.fromkeys(norm(x) for x in names if 1<len(norm(x).split())<=12))
alias={d['url']:name_alias(d) for d in knowledge}
# Extract actual sections from the pinned HTML, not title-only summaries.
def profile(d):
    s=BeautifulSoup(Path(d['file']).read_text(encoding='utf-8'),'html.parser')
    area=s.select_one('.article-body') or s.select_one('.lv-content') or s.select_one('main')
    assert area is not None,d['url']
    ac=BeautifulSoup(str(area),'html.parser')
    for n in ac.select('script,style,nav,aside,footer,header,.ux-outline'):n.decompose()
    sections=[];cur={'heading':label(d),'level':1,'id':'','paragraphs':[]}
    def flush():
        if cur['paragraphs']:
            p=cur['paragraphs']
            sections.append(dict(heading=cur['heading'],level=cur['level'],id=cur['id'],paragraph_count=len(p),word_count=sum(len(t.split()) for t in p),evidence=p[0][:800],paragraphs=p))
    for n in ac.select('h1,h2,h3,h4,p,li,pre,blockquote,table'):
        if n.find_parent(['li','pre','blockquote','table']):continue
        t=clean(n.get_text(' ',strip=True))
        if not t:continue
        if n.name in ('h1','h2','h3','h4'):
            flush();cur={'heading':t,'level':int(n.name[1]),'id':n.get('id',''),'paragraphs':[]}
        else:cur['paragraphs'].append(t)
    flush()
    if not sections:sections=[dict(heading=label(d),level=1,id='',paragraph_count=1,word_count=len(d['body'].split()),evidence=d['body'][:800],paragraphs=[d['body']])]
    # Extract evidence-bearing explicit lexical matches. These are candidate mentions, not entity disambiguation.
    mentions=[]
    for target,names in alias.items():
        if target==d['url'] or not names:continue
        hits=[]
        for sec in sections:
            for para in sec['paragraphs']:
                nt=norm(para)
                hit=next((a for a in names if ' '+a+' ' in ' '+nt+' '),None)
                if hit:
                    hits.append(dict(section=sec['heading'],anchor_id=sec['id'],alias=hit,excerpt=para[:700]))
                    break
            if len(hits)>=3:break
        if hits:mentions.append(dict(target=target,evidence=hits))
    citations=[]
    for a in ac.select('a[href]'):
        h=a['href'];u=urlsplit(h)
        if u.scheme in ('https','http') and u.netloc not in ('levenshtein.net','www.levenshtein.net','levenshteinv2.github.io'):
            citations.append(dict(url=h,anchor=clean(a.get_text(' ',strip=True))))
    citations=list({x['url']:x for x in citations}.values())
    return dict(url=d['url'],title=d.get('title'),h1=d.get('h1'),group=d['group'],provisional_mission=d['mission'],content_sha256=d['content_sha256'],canonical=d.get('canonical'),primary_entity_candidate=label(d),intent_hypothesis=('reference/navigation' if d['group']=='Legacy' or d['url'] in hubs else 'informational/technical'),review_status='machine_extracted_pending_ai_review',sections=sections,explicit_mention_candidates=mentions,schema_entities=d.get('entities',[]),schema_relations=d.get('schema_relations',[]),external_citations=citations)
hubs={'/','/foundations','/algorithms','/theory','/implementations','/comparisons','/history','/papers','/applications','/search','/data-matching','/language-processing','/bioinformatics','/coding-theory','/software-systems','/text-tools','/unicode-text-tools'}
sem_scopes={'contextual','main_content','listing_related'}
pairs={(e['source'],e['target']) for e in links}
sem={(e['source'],e['target']) for e in links if e['scope'] in sem_scopes}
context={(e['source'],e['target']) for e in links if e['scope']=='contextual'}
def ws1_2():
    with ThreadPoolExecutor(max_workers=6) as pool:profiles=list(pool.map(profile,knowledge))
    for p in profiles:(P/(safe(p['url'])+'.json')).write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    registry=[dict(url=p['url'],group=p['group'],mission=p['provisional_mission'],entity_candidate=p['primary_entity_candidate'],intent_hypothesis=p['intent_hypothesis'],sections=len(p['sections']),mentions=len(p['explicit_mention_candidates']),external_sources=len(p['external_citations']),status=p['review_status'],hash=p['content_sha256']) for p in profiles]
    csvout('ws1-page-profiles.csv',registry)
    # Existing schema edges, lexical mentions and suggested relations deliberately kept distinct.
    es=[dict(source=p['url'],subject=str(a),relation=str(b),object=str(c),evidence_kind='schema_assertion_not_verified') for p in profiles for a,b,c in p['schema_relations']]
    csvout('ws2-schema-assertions.csv',es)
    mention_rows=[dict(source=p['url'],target=m['target'],section=e['section'],anchor_id=e['anchor_id'],matched_alias=e['alias'],excerpt=e['excerpt'],existing_contextual=(p['url'],m['target']) in context) for p in profiles for m in p['explicit_mention_candidates'] for e in m['evidence']]
    csvout('ws2-mention-evidence.csv',mention_rows)
    return profiles,registry,es,mention_rows
def ws3():
    # TF-IDF cosine and exact heading overlap; lexical signals only, not cannibalization or semantic verdicts.
    corp={d['url']:collections.Counter(tokens(d['body'])) for d in knowledge}
    df=collections.Counter(k for c in corp.values() for k in c)
    vect={r:{k:(1+math.log(v))*math.log((len(corp)+1)/(df[k]+1)) for k,v in c.items()} for r,c in corp.items()}
    normv={r:math.sqrt(sum(v*v for v in c.values())) or 1 for r,c in vect.items()}
    heads={d['url']:{norm(h) for h in d.get('headings',[]) if len(tokens(h))>=3} for d in knowledge}
    out=[]
    for a,b in itertools.combinations(corp,2):
        va,vb=vect[a],vect[b];shared=va.keys()&vb.keys()
        sim=sum(va[k]*vb[k] for k in shared)/(normv[a]*normv[b])
        hshared=heads[a]&heads[b];j=len(hshared)/max(1,len(heads[a]|heads[b]))
        top=sorted(shared,key=lambda k:va[k]*vb[k],reverse=True)[:8]
        out.append(dict(a=a,b=b,group_a=by[a]['group'],group_b=by[b]['group'],cosine=round(sim,4),heading_jaccard=round(j,4),common_headings=' | '.join(sorted(hshared)[:8]),shared_terms=' '.join(top),status='lexical_candidate_not_cannibalization'))
    out.sort(key=lambda x:(x['cosine'],x['heading_jaccard']),reverse=True)
    csvout('ws3-all-pair-scores.csv',out)
    shortlist=[x for x in out if x['cosine']>=.30 or x['heading_jaccard']>=.20]
    csvout('ws3-overlap-review-queue.csv',shortlist)
    return out,shortlist
def ws4_5(profiles):
    pm={p['url']:p for p in profiles}
    rows=[]
    for p in proposals:
        a,b=p['source'],p['target']
        hit=next((m['evidence'][0] for m in pm.get(a,{}).get('explicit_mention_candidates',[]) if m['target']==b),{})
        scope=sorted({e['scope'] for e in links if (e['source'],e['target'])==(a,b)})
        # Existing navigation links are not automatically deficient. No forced reciprocal edges.
        state='content_link_exists' if (a,b) in sem else 'navigation_only_review' if (a,b) in pairs else 'missing_link_review'
        priority='P1' if p['relation']=='supported_by' and state!='content_link_exists' else 'P2' if hit and state!='content_link_exists' else 'P3'
        rows.append(dict(source=a,target=b,relation=p['relation'],state=state,priority=priority,scopes=' | '.join(scope),section=hit.get('section',''),anchor_id=hit.get('anchor_id',''),excerpt=hit.get('excerpt',''),reason=p['reason'],status='requires_ai_review'))
    csvout('ws4-link-review-queue.csv',rows)
    gaps=[]
    for p in profiles:
        r=p['url'];inc=sum(b==r for a,b in sem);out=sum(a==r for a,b in sem)
        # Internal coverage flags, not definitive content gaps.
        if inc==0 or out==0:gaps.append(dict(url=r,kind='no_content_inbound' if inc==0 else 'no_content_outbound',evidence=f'in={inc};out={out}',status='review_scope_and_intent'))
        if r not in hubs and by[r]['group'] not in ('Legacy',) and not p['external_citations']:gaps.append(dict(url=r,kind='no_external_citation_in_extracted_content',evidence='0 detected external anchors',status='review_before_claiming_gap'))
        if r not in hubs and by[r]['group'] not in ('Legacy',) and not p['schema_entities']:gaps.append(dict(url=r,kind='no_page_local_schema_entity_detected',evidence='0 matching page entity objects',status='review_schema_not_ranking_claim'))
    for p in rows:
        if p['relation']=='supported_by' and p['state']!='content_link_exists':gaps.append(dict(url=p['source'],kind='research_evidence_link_candidate',evidence=p['target'],status='review_original_text_and_citation'))
    csvout('ws5-coverage-flags.csv',gaps)
    return rows,gaps
with ThreadPoolExecutor(max_workers=2) as ex:
    a=ex.submit(ws1_2);b=ex.submit(ws3)
    profiles,registry,es,mentions=a.result();scores,short=b.result()
rows,gaps=ws4_5(profiles)
# Produce bounded review packets, complete section index + representative original excerpts, not a substitute for full text.
packetdir=OUT/'review-packets';packetdir.mkdir(exist_ok=True)
clusters=collections.defaultdict(list)
for p in profiles:clusters[p['group']].append(p)
for g,ps in clusters.items():
    packet=[]
    for p in ps:
        secs=p['sections']
        sample=secs if len(secs)<=10 else secs[:4]+secs[4:-2: max(1,(len(secs)-6)//4)][:4]+secs[-2:]
        packet.append(dict(url=p['url'],mission=p['provisional_mission'],h1=p['h1'],entity_candidate=p['primary_entity_candidate'],hash=p['content_sha256'],section_index=[x['heading'] for x in secs],sample_evidence=[dict(section=x['heading'],id=x['id'],excerpt=x['evidence'][:500]) for x in sample],mentions=[dict(target=x['target'],evidence=x['evidence'][:1]) for x in p['explicit_mention_candidates'][:12]],top_overlap=[x for x in scores if p['url'] in (x['a'],x['b'])][:3],link_candidates=[x for x in rows if x['source']==p['url'] and x['state']!='content_link_exists'][:8]))
    (packetdir/(g+'.json')).write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# QA: each profile references actual extracted evidence, source fingerprints unchanged; no claim of AI review.
assert len(profiles)==91 and len(scores)==91*90//2
assert {p['url'] for p in profiles}=={d['url'] for d in knowledge}
assert all(p['sections'] and p['content_sha256']==by[p['url']]['content_sha256'] for p in profiles)
assert all(e['source'] in by and e['target'] in by for e in rows)
summary=dict(snapshot='528b3f6539411d1629164ddd7460d6a4ac0fafb3',knowledge_pages=91,tool_boundary_nodes=17,profiles=len(profiles),sections=sum(len(p['sections']) for p in profiles),schema_assertions=len(es),mention_evidence=len(mentions),pairwise_comparisons=len(scores),lexical_overlap_candidates=len(short),link_relationship_candidates=len(rows),missing_content_links=sum(x['state']!='content_link_exists' for x in rows),p1_research_links=sum(x['priority']=='P1' for x in rows),coverage_flags=len(gaps),review_packets=len(clusters),ai_reviewed=0,ws6_machine_gate='PASS',ws6_semantic_gate='PENDING_AI_REVIEW',production_changes=0,tool_changes=0)
save('summary.json',summary)
save('review-state.json',dict(pages=[dict(url=p['url'],hash=p['content_sha256'],status='pending_ai_review',reviewer=None) for p in profiles],rules=['Củng cố entity','Nối entity','No deployment until evidence-backed review','Do not add links solely on lexical similarity','Preserve 17 tools and production']))
(OUT/'README.md').write_text("""# Entity Intelligence V1
Two governing objectives: củng cố Entity; nối Entity.
WS1: per-page full section evidence and provisional mission. WS2: separate schema assertions and lexical mention candidates. WS3: all 4,095 pairwise lexical comparisons, not proof of cannibalization. WS4: actual vs proposed link relationship queue; no automatic edits. WS5: coverage flags, not verified knowledge gaps. WS6: deterministic coverage and provenance gate; semantic review is separate and explicitly pending.
Review by cluster using review-packets, full profile JSON and source HTML when needed. A reviewer must record distinct mission, main and supporting entities, intent hypothesis, boundary against related pages, evidence section/excerpt, approved/rejected links with placement, uncertainties and content hash. Never mark reviewed solely because a script ran. Reuse unchanged hashes; re-review only changed pages and affected relations. All files on audit branch; no website publication.
""",encoding='utf-8')
print('INTELLIGENCE SUMMARY',json.dumps(summary,ensure_ascii=False))
print('TOP OVERLAP',json.dumps(scores[:12],ensure_ascii=False))
print('P1 LINKS',json.dumps([dict(source=x['source'],target=x['target'],section=x['section']) for x in rows if x['priority']=='P1'],ensure_ascii=False))
