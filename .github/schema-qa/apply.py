import json,re,subprocess,hashlib,copy
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
R=Path('.github/schema-qa')
reg=json.loads((R/'registry.json').read_text())
BASE=reg['snapshot']
manifest=json.loads(Path('.github/qa/pages.json').read_text())
assert len(manifest)==len(set(manifest))==91
ORIGIN='https://www.levenshtein.net'
def route(p):return '/' if p=='index.html' else '/'+p.removesuffix('.html')
def walk(x):
 if isinstance(x,dict):
  yield x
  for k,v in x.items():
   if k!='@context':yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def types(x):
 t=x.get('@type',[])
 return [t] if isinstance(t,str) else t
def js(s):return json.dumps(s,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
pat=re.compile(r'(<script\b[^>]*\btype=["\']application/ld\+json["\'][^>]*>)([\s\S]*?)(</script>)',re.I)
counts=Counter();results=[]
def ids(doc):return Counter(n['@id'] for n in walk(doc) if isinstance(n.get('@id'),str))
allowedtypes={'WebPage','CollectionPage','AboutPage','TechArticle','Article','BlogPosting'}
def mask(x):
 for n in walk(x):
  if isinstance(n.get('@id'),str) and types(n):
   n.pop('name',None);n.pop('description',None)
 return x
def expected(n,r,desc):
 ident=n.get('@id');ts=types(n);out={}
 if not isinstance(ident,str) or not ts:return out
 if ident in reg['core'] and 'DefinedTerm' in ts:
  out.update({k:reg['core'][ident][k] for k in ('name','description') if k in n})
 if ident in reg['ownerNames'] and 'name' in n:out['name']=reg['ownerNames'][ident]
 if ident in reg['conceptNames'] and 'DefinedTerm' in ts and 'name' in n:out['name']=reg['conceptNames'][ident]
 if ident.startswith(ORIGIN+'/') and urlsplit(ident).path==r and set(ts)&allowedtypes and isinstance(n.get('description'),str):out['description']=desc
 return out
for p in manifest:
 old=Path(p).read_bytes().decode('utf-8');assert old==subprocess.check_output(['git','show',BASE+':'+p]).decode('utf-8'),p
 r=route(p);s=BeautifulSoup(old,'html.parser');desc=s.find('meta',attrs={'name':'description'})['content'];changes=Counter()
 def patch(match):
  doc=json.loads(match[2]);orig=copy.deepcopy(doc)
  for n in walk(doc):
   for k,v in expected(n,r,desc).items():
    if n[k]!=v:
     ident=n['@id'];kind='core' if ident in reg['core'] else 'owner' if ident in reg['ownerNames'] and k=='name' else 'concept' if ident in reg['conceptNames'] else 'own'
     n[k]=v;changes[kind+'_'+k]+=1
  assert ids(orig)==ids(doc)
  assert mask(copy.deepcopy(orig))==mask(copy.deepcopy(doc)),p
  return match[1]+js(doc)+match[3] if doc!=orig else match[0]
 new=pat.sub(patch,old)
 assert pat.sub('',old)==pat.sub('',new),(p,'non-jsonld bytes changed')
 if new!=old:
  Path(p).write_bytes(new.encode('utf-8'));counts.update(changes);results.append(dict(path=p,changes=dict(changes),old_sha256=hashlib.sha256(old.encode()).hexdigest(),new_sha256=hashlib.sha256(new.encode()).hexdigest()))
diff=subprocess.check_output(['git','diff','--name-only',BASE]).decode().splitlines()
assert all(p in manifest or p.startswith('.github/schema-qa/') or p=='.github/workflows/schema-core-staging.yml' for p in diff)
assert set(p for p in diff if p in manifest)==set(x['path'] for x in results)
errors=[];nodes=0
for p in manifest:
 r=route(p);s=BeautifulSoup(Path(p).read_text(),'html.parser');desc=s.find('meta',attrs={'name':'description'})['content']
 for tag in s.select('script[type="application/ld+json"]'):
  doc=json.loads(tag.string or tag.get_text())
  for n in walk(doc):
   if isinstance(n.get('@id'),str) and types(n):nodes+=1
   for k,v in expected(n,r,desc).items():
    if n[k]!=v:errors.append([p,n.get('@id'),k])
assert not errors,errors
report=dict(snapshot=BASE,knowledge_pages=91,changed_pages=len(results),unchanged_pages=91-len(results),changes=dict(counts),all_id_occurrences_preserved=True,all_non_jsonld_bytes_preserved=True,all_other_schema_fields_preserved=True,registry_mismatches=len(errors),typed_identified_nodes=nodes,tool_changes=0,gate='PASS',scope='Scoped name/description normalization only; no vocabulary, provenance or Google Rich Results certification.',results=results)
(R/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False))
