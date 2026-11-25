import json,re,html,subprocess,hashlib,statistics
from pathlib import Path
from bs4 import BeautifulSoup
R=Path('.github/metadata-qa')
reg=json.loads((R/'registry.json').read_text())
BASE=reg['base']
rows={r['path']:r for r in reg['rows']}
manifest=json.loads(Path('.github/qa/pages.json').read_text())
assert len(rows)==len(manifest)==91 and set(rows)==set(manifest)
def norm(s):return ' '.join(s.casefold().split())
def stats(v):return dict(min=min(v),max=max(v),mean=round(statistics.mean(v),2))
def getmeta(s,key):
 a=s.find_all('meta',attrs={('property' if key.startswith('og:') else 'name'):key})
 assert len(a)==1,(key,len(a))
 return a[0]['content']
def patch(head,key,val):
 mode='property' if key.startswith('og:') else 'name'
 pattern=r'<meta\b(?=[^>]*\b'+mode+r'=["\']'+re.escape(key)+r'["\'])[^>]*>'
 hits=list(re.finditer(pattern,head,re.I))
 assert len(hits)==1,(key,len(hits))
 old=hits[0][0]
 new,n=re.subn(r'\bcontent=(["\'])(.*?)\1',lambda m:'content="'+html.escape(val,quote=True)+'"',old,count=1,flags=re.S|re.I)
 assert n==1,(key,old)
 return head[:hits[0].start()]+new+head[hits[0].end():]
keys=['description','og:title','og:description','twitter:title','twitter:description']
results=[]
for p in manifest:
 old=Path(p).read_bytes().decode('utf-8')
 assert old==subprocess.check_output(['git','show',BASE+':'+p]).decode('utf-8'),(p,'baseline drift')
 head,body=old.split('</head>',1)
 a=BeautifulSoup(head+'</head>','html.parser')
 old_title=a.title.get_text();old_desc=getmeta(a,'description')
 title,desc=rows[p]['title'],rows[p]['description']
 assert 50<=len(title)<=60 and 140<=len(desc)<=160,(p,len(title),len(desc))
 assert len(a.find_all('title'))==1
 new,n=re.subn(r'<title>[\s\S]*?</title>',lambda m:'<title>'+html.escape(title,quote=False)+'</title>',head,count=1,flags=re.I)
 assert n==1
 for key in keys:new=patch(new,key,title if key.endswith(':title') else desc)
 b=BeautifulSoup(new+'</head>','html.parser')
 assert b.title.get_text()==title
 assert all(getmeta(b,k)==(title if k.endswith(':title') else desc) for k in keys)
 for s in (a,b):
  s.title.decompose()
  for key in keys:s.find('meta',attrs={('property' if key.startswith('og:') else 'name'):key}).decompose()
 assert str(a)==str(b),(p,'unauthorized head delta')
 out=new+'</head>'+body
 assert out.split('</head>',1)[1]==body
 Path(p).write_bytes(out.encode('utf-8'))
 results.append(dict(path=p,old_title=old_title,old_description=old_desc,new_title=title,new_description=desc,old_title_chars=len(old_title),old_description_chars=len(old_desc),title_chars=len(title),description_chars=len(desc),body_sha256=hashlib.sha256(body.encode()).hexdigest(),changed=out!=old))
assert len({norm(x['new_title']) for x in results})==91
assert len({norm(x['new_description']) for x in results})==91
changed=subprocess.check_output(['git','diff','--name-only',BASE]).decode().splitlines()
assert all(p in manifest or p.startswith('.github/metadata-qa/') or p=='.github/workflows/metadata-staging.yml' for p in changed),changed
summary=dict(base=BASE,pages=91,changed_pages=sum(x['changed'] for x in results),before=dict(title_in_range=sum(50<=x['old_title_chars']<=60 for x in results),description_in_range=sum(140<=x['old_description_chars']<=160 for x in results),title=stats([x['old_title_chars'] for x in results]),description=stats([x['old_description_chars'] for x in results])),after=dict(title_in_range=91,description_in_range=91,unique_titles=91,unique_descriptions=91,title=stats([x['title_chars'] for x in results]),description=stats([x['description_chars'] for x in results])),body_unchanged=91,canonical_robots_schema_unchanged=91,social_metadata_synced=91,gate='PASS',scope='91 knowledge pages; 17 tools excluded; no deployment',limitations=['Character counts are editorial targets, not Google ranking rules or pixel-width guarantees.','Full semantic relevance and live SERP title rewrite behavior not certified.','Legacy legal content and language tags unchanged; about.htm has mixed English/German content.'])
(R/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(R/'before-after.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
