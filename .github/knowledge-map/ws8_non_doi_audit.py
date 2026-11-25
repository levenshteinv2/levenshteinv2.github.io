"""Bounded, read-only external reference accessibility check; no automatic edits."""
import concurrent.futures,collections,json,re,urllib.parse,urllib.request,urllib.error,pathlib,time
from html.parser import HTMLParser
P=pathlib.Path
out=P("qa-report");out.mkdir(exist_ok=True)
q=json.loads(P(".github/knowledge-map/intelligence/ws8/external-reference-queue.json").read_text())
manifest=json.loads(P("site/.github/qa/pages.json").read_text())
assert len(manifest)==len(set(manifest))==91
routes={"/" if p=="index.html" else "/"+p.removesuffix(".html") for p in manifest}
hosts={"www.levenshtein.net","levenshtein.net","levenshteinv2.github.io"}
groups=collections.defaultdict(list)
for r in q:
 u=urllib.parse.urlsplit(r["target"])
 if r["route"] in routes and u.scheme in ("http","https") and u.hostname not in hosts|{"doi.org","dx.doi.org"}:
  groups[r["target"]].append({"page":r["route"],"property":r["property"],"node":r["node"]})
assert len(groups)==63,len(groups)
class Title(HTMLParser):
 def __init__(self):
  super().__init__();self.in_title=False;self.parts=[]
 def handle_starttag(self,t,a):
  if t=="title":self.in_title=True
 def handle_endtag(self,t):
  if t=="title":self.in_title=False
 def handle_data(self,d):
  if self.in_title:self.parts.append(d)
def check(target):
 row={"target":target,"references":groups[target]}
 # One GET per destination, limited body. No authentication, no evasion.
 try:
  req=urllib.request.Request(target,headers={"User-Agent":"Levenshtein reference QA (https://github.com/levenshteinv2/levenshteinv2.github.io)","Accept":"text/html,application/pdf,*/*;q=0.5"})
  with urllib.request.urlopen(req,timeout=15) as f:
   ct=f.headers.get("Content-Type","");body=f.read(196608)
   row.update(http=f.status,final=f.geturl(),content_type=ct)
   if "html" in ct.lower():
    parser=Title();parser.feed(body.decode(f.headers.get_content_charset() or "utf-8",errors="replace"));row["title"]=" ".join(" ".join(parser.parts).split())[:350]
   row["status"]="accessible" if 200<=f.status<300 else "review"
   if re.search(r"access denied|just a moment|captcha|page not found|request blocked|robot check",row.get("title",""),re.I):row["status"]="access_or_soft_error_review"
 except urllib.error.HTTPError as e:row.update(http=e.code,final=e.geturl(),status="http_review")
 except Exception as e:row.update(status="network_review",detail=str(e))
 return row
# Group by host so requests to a single host are sequential and rate-limited.
by_host=collections.defaultdict(list)
for u in groups:by_host[urllib.parse.urlsplit(u).hostname].append(u)
def host_batch(urls):
 rows=[]
 for u in urls:
  rows.append(check(u));time.sleep(.6)
 return rows
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for batch in pool.map(host_batch,by_host.values()):rows.extend(batch)
rows.sort(key=lambda x:x["target"])
summary={"scope":"91 knowledge pages; non-DOI external schema references only; 1 same-site citation excluded","targets":len(groups),"processed":len(rows),"status":dict(collections.Counter(x["status"] for x in rows)),"note":"HTTP 2xx is accessibility evidence, not semantic certification. Errors are review candidates; no automated removal or replacement."}
(out/"non-doi-results.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(out/"non-doi-summary.json").write_text(json.dumps(summary,indent=2))
print("NONDOI SUMMARY",json.dumps(summary),flush=True)
for r in rows:
 if r["status"]!="accessible":print("NONDOI REVIEW",json.dumps({k:v for k,v in r.items() if k!="references"},ensure_ascii=False),flush=True)
