"""Final broad knowledge audit. No site edits; hard defects separated from review items."""
import collections,json,pathlib,re,urllib.parse,urllib.request,subprocess
from bs4 import BeautifulSoup
from outbound_nofollow import external,run
P=pathlib.Path
pages=json.loads(P('.github/qa/pages.json').read_text())
assert len(pages)==len(set(pages))==91
hosts={'www.levenshtein.net','levenshtein.net','levenshteinv2.github.io'}
out=P('qa-report');out.mkdir(exist_ok=True)
errors=[];reviews=[];rows=[];defs=set();refs=[];used_types=set();used_props=set()
titles=collections.defaultdict(list);descs=collections.defaultdict(list);canonicals=collections.defaultdict(list)
def flag(p,k,d,hard=True): (errors if hard else reviews).append({'page':p,'code':k,'detail':d})
def route(p):return '/' if p=='index.html' else '/'+p.removesuffix('.html')
def normalized_path(p):
 return urllib.parse.unquote(p or '/').removesuffix('/index.html').removesuffix('.html').rstrip('/') or '/'
def walk(n):
 if isinstance(n,dict):
  yield n
  for k,v in n.items():
   if k!='@context':yield from walk(v)
 elif isinstance(n,list):
  for v in n:yield from walk(v)
def norm(s):return ' '.join((s or '').split())
soups={p:BeautifulSoup(P(p).read_text(encoding='utf-8'),'html.parser') for p in pages}
routes={route(p):p for p in pages}
known_tools=set('/'+s for s in 'fancy-text-generator schriftgenerator generador-de-letras letras-diferentes font-henkan krasivyy-shrift ki-tu-dac-biet letras-bonitas yazi-stilleri font-style te-shu-zi-ti caratteri-speciali akson-phiset font-aesthetic lettertypes police-d-ecriture generator-czcionek'.split())
for p,s in soups.items():
 r=route(p); title=norm(s.title.get_text() if s.title else '')
 ds=s.select('meta[name="description"]');desc=norm(ds[0].get('content') if len(ds)==1 else '')
 can=s.select('link[rel="canonical"]');url=can[0].get('href','') if len(can)==1 else ''
 u=urllib.parse.urlsplit(url);robots=' '.join(t.get('content','') for t in s.select('meta[name="robots"]')).lower()
 if not title or len(s.select('title'))!=1:flag(p,'title','missing or duplicate')
 if not desc or len(ds)!=1:flag(p,'description','missing or duplicate')
 if len(can)!=1 or u.scheme!='https' or u.hostname!='www.levenshtein.net' or normalized_path(u.path)!=r or u.query or u.fragment:flag(p,'canonical',url)
 if 'noindex' not in re.split(r'[\s,]+',robots):flag(p,'preview_noindex',robots)
 if len(s.select('h1'))!=1:flag(p,'h1','not exactly one')
 expected_lang='de' if p=='privacy.htm' else 'en'
 if not s.html or s.html.get('lang','').split('-')[0]!=expected_lang:flag(p,'language',s.html.get('lang') if s.html else None)
 titles[title.casefold()].append(p);descs[desc.casefold()].append(p);canonicals[normalized_path(u.path)].append(p)
 if not 30<=len(title)<=65:flag(p,'title_length_advisory',len(title),False)
 if not 70<=len(desc)<=165:flag(p,'description_length_advisory',len(desc),False)
 _,nf=run(P(p).read_text(encoding='utf-8'),False)
 if nf['missing_after']:flag(p,'nofollow',nf['missing_after'])
 ids=collections.Counter(t['id'] for t in s.select('[id]'))
 for id,n in ids.items():
  if n>1:flag(p,'duplicate_html_id',id)
 lc=0;tool_links=0
 for a in s.select('a[href],area[href]'):
  h=a.get('href','').strip();q=urllib.parse.urlsplit(h)
  if external(h) or q.scheme not in ('','http','https'):continue
  if q.netloc and q.hostname not in hosts:continue
  v=urllib.parse.urlsplit(urllib.parse.urljoin('https://www.levenshtein.net'+r,h))
  dest=normalized_path(v.path);target=routes.get(dest)
  if dest in known_tools:tool_links+=1;continue
  if target:
   lc+=1
   if v.fragment and not v.fragment.startswith(':~:text='):
    frag=urllib.parse.unquote(v.fragment)
    if not soups[target].find(id=frag) and not soups[target].find('a',attrs={'name':frag}):flag(p,'missing_fragment',h)
  elif not any(x.is_file() for x in [P(v.path.lstrip('/')),P(v.path.lstrip('/')+'.html'),P(v.path.lstrip('/'))/'index.html']):
   flag(p,'unresolved_internal_href',h)
 scripts=s.select('script[type="application/ld+json"]')
 for tag in scripts:
  try:j=json.loads(tag.string or tag.get_text())
  except Exception as e:flag(p,'jsonld_parse',str(e));continue
  for n in walk(j):
   i=n.get('@id');t=n.get('@type',[])
   if isinstance(t,str):t=[t]
   if isinstance(t,list):used_types.update(x for x in t if isinstance(x,str))
   used_props.update(k for k in n if not k.startswith('@'))
   if isinstance(i,str):
    if set(n)-{'@id','@context'}:defs.add(i)
    else:refs.append((p,i))
 if not scripts:flag(p,'optional_no_jsonld','No structured data; not automatically a defect',False)
 rows.append({'page':p,'title':title,'title_length':len(title),'description_length':len(desc),'canonical':url,'outbound_links':nf['external'],'nofollow_missing':nf['missing_after'],'knowledge_links':lc,'tool_links_read_only':tool_links,'jsonld_scripts':len(scripts)})
for k,d in [('duplicate_title',titles),('duplicate_description',descs),('duplicate_canonical',canonicals)]:
 for v,paths in d.items():
  if len(paths)>1:flag(paths[0],k,paths)
for p,i in refs:
 if i.startswith('https://www.levenshtein.net/') and i not in defs:
  dest=normalized_path(urllib.parse.urlsplit(i).path)
  flag(p,'schema_reference_review' if dest not in routes else 'unresolved_knowledge_id',i,dest in routes)
vocab={'status':'NOT_RUN'}
try:
 req=urllib.request.Request('https://schema.org/version/latest/schemaorg-current-https.jsonld',headers={'User-Agent':'Levenshtein knowledge QA'})
 with urllib.request.urlopen(req,timeout=25) as f: doc=json.load(f)
 classes=set();props=set()
 for n in doc.get('@graph',[]):
  i=n.get('@id',''); t=n.get('@type',[]);t=[t] if isinstance(t,str) else t
  name=i.removeprefix('schema:').removeprefix('https://schema.org/').removeprefix('http://schema.org/')
  if 'rdfs:Class' in t:classes.add(name)
  if 'rdf:Property' in t:props.add(name)
 assert len(classes)>500 and len(props)>500
 unknown_types=sorted(used_types-classes);unknown_props=sorted(used_props-props)
 vocab={'status':'REVIEW' if unknown_types or unknown_props else 'PASS','classes':len(classes),'properties':len(props),'unknown_types':unknown_types,'unknown_properties':unknown_props,'scope':'Vocabulary term membership only; not rich-result eligibility or domain/range validation'}
except Exception as e:vocab={'status':'UNAVAILABLE','detail':str(e)}
report={'snapshot':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'pages':len(rows),'hard_issues':len(errors),'hard_codes':dict(collections.Counter(x['code'] for x in errors)),'review_codes':dict(collections.Counter(x['code'] for x in reviews)),'external_links':sum(x['outbound_links'] for x in rows),'nofollow_missing':sum(x['nofollow_missing'] for x in rows),'knowledge_links':sum(x['knowledge_links'] for x in rows),'unique_schema_ids':len(defs),'vocabulary':vocab,'errors':errors,'reviews':reviews,'rows':rows}
(out/'knowledge-closure.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('errors','reviews','rows')},ensure_ascii=False))
for x in errors[:120]:print('CLOSURE ISSUE',json.dumps(x,ensure_ascii=False))
if errors:raise SystemExit(1)
