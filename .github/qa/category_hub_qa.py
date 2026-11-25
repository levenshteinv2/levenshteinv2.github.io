"""Validate curated category hubs against the locked baseline, then test rendered pages."""
import asyncio,collections,json,pathlib,re,subprocess,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from outbound_nofollow import external,run
P=pathlib.Path
BASE="b1eb725c97ecde57d5a0030d934f30605be12080"
SLUGS="foundations algorithms applications theory implementations comparisons history papers search data-matching language-processing bioinformatics coding-theory software-systems text-tools unicode-text-tools".split()
PAGES=[x+".html" for x in SLUGS]
HOST="https://www.levenshtein.net"
CHILDREN=["/search","/data-matching","/language-processing","/bioinformatics","/coding-theory","/software-systems"]
def path(v):
 if not isinstance(v,str):return None
 return urlsplit(v).path.removesuffix(".html").rstrip("/") or "/"
def graph(s):
 return [n for script in s.select('script[type="application/ld+json"]') for n in json.loads(script.string or script.get_text())["@graph"]]
def items(n):
 assert n["numberOfItems"]==len(n["itemListElement"])
 assert [x["position"] for x in n["itemListElement"]]==list(range(1,len(n["itemListElement"])+1))
 return [path((x.get("item") or {}).get("@id") or (x.get("item") or {}).get("url") or x.get("url")) for x in n["itemListElement"]]
def metadata(s):
 return [str(x) for x in s.select("title,meta,link[rel=canonical],link[rel=alternate]")]
def normalized_card(x):
 x=BeautifulSoup(str(x),"html.parser")
 for y in x.select(".lv-post__no"):y.string="N"
 return str(x)
def tool_cards(s):return [str(x) for x in s.select("main a.lv-tool-card")]
rows=[]
for slug,file in zip(SLUGS,PAGES):
 old=subprocess.check_output(["git","show",BASE+":"+file],text=True)
 new=P(file).read_text(encoding="utf-8")
 a,b=(BeautifulSoup(x,"html.parser") for x in (old,new))
 assert metadata(a)==metadata(b),file
 assert len(b.select("h1"))==1,file
 assert str(a.select_one("aside"))==str(b.select_one("aside")),file
 assert tool_cards(a)==tool_cards(b),file
 assert not run(new,False)[1]["missing_after"],file
 g=graph(b)
 own=[n for n in g if n.get("@type")=="CollectionPage" and path(n.get("@id"))=="/"+slug]
 assert len(own)==1,file
 lists=[n for n in g if n.get("@type")=="ItemList" and path(n.get("@id"))=="/"+slug]
 oldcards=a.select("main ol.lv-posts > li.lv-post")
 newcards=b.select("main ol.lv-posts > li.lv-post")
 assert collections.Counter(map(normalized_card,oldcards))==collections.Counter(map(normalized_card,newcards)),file
 actual=[path(c.select_one("h3 a")["href"]) for c in newcards]
 assert len(actual)==len(set(actual)),file
 assert [c.select_one(".lv-post__no").get_text(strip=True) for c in newcards]==[str(i).zfill(2) for i in range(1,len(actual)+1)],file
 if slug=="applications":
  primary=next(n for n in lists if n["@id"].endswith("#itemlist"))
  selected=next(n for n in lists if n["@id"].endswith("#selected-articles"))
  assert items(primary)==CHILDREN,file
  shown=[path(x["href"]) for x in b.select(".lv-page-intro ol li a[href]")]
  assert shown==CHILDREN,file
  assert items(selected)==actual,file
 elif slug=="unicode-text-tools":
  assert len(tool_cards(b))==17,file
  assert len(lists)==1 and items(lists[0])==[path(x["href"]) for x in b.select("main a.lv-tool-card")],file
  assert own[0]["isPartOf"]["@id"]==HOST+"/text-tools#webpage",file
 elif slug=="text-tools":
  assert len(tool_cards(b))==17 and items(lists[0])==["/unicode-text-tools"],file
 else:
  assert len(lists)==1 and items(lists[0])==actual,file
  if slug=="language-processing":assert len(actual)==7,file
 for n in lists:
  assert len(items(n))==len(set(items(n))),file
 assert b.select_one(".lv-page-intro").get_text(" ",strip=True),file
 rows.append({"page":file,"cards":len(actual),"tool_cards":len(tool_cards(b)),"lists":len(lists),"status":"PASS"})
changed=set(subprocess.check_output(["git","diff","--name-only",BASE,"HEAD"],text=True).splitlines())
assert changed-set(PAGES)=={".github/qa/category_hub_qa.py",".github/workflows/category-hub-qa.yml"},changed-set(PAGES)
assert set(PAGES)<=changed
print("CATEGORY STATIC",json.dumps({"pages":len(rows),"article_cards":sum(x["cards"] for x in rows),"results":rows},ensure_ascii=False),flush=True)
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  p=super().translate_path(path)
  if not P(p).exists() and P(p+".html").is_file():return p+".html"
  return p
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
origin="http://127.0.0.1:"+str(server.server_port)
async def browser_checks():
 results=[]
 async with async_playwright() as pw:
  for engine in ["chromium","firefox","webkit"]:
   browser=await getattr(pw,engine).launch()
   sem=asyncio.Semaphore(3)
   async def test(file,w,h):
    async with sem:
     ctx=await browser.new_context(viewport={"width":w,"height":h})
     errors=[]
     try:
      page=await ctx.new_page()
      page.on("pageerror",lambda e:errors.append(str(e)))
      await ctx.route("**/*",lambda r:r.continue_() if r.request.url.startswith(origin+"/") else r.abort())
      response=await page.goto(origin+"/"+file,wait_until="domcontentloaded",timeout=25000)
      await page.evaluate("Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,1000))])")
      d=await page.evaluate("""() => ({w:document.documentElement.scrollWidth,viewport:innerWidth,h1:document.querySelectorAll('h1').length,links:[...document.querySelectorAll('a[href],area[href]')].map(a=>({href:a.getAttribute('href'),rel:a.getAttribute('rel')||''}))})""")
      if not response or response.status!=200:errors.append("HTTP")
      if d["w"]>w+2:errors.append("horizontal overflow")
      if d["h1"]!=1:errors.append("h1")
      if any(external(a["href"] or "") and "nofollow" not in a["rel"].lower().split() for a in d["links"]):errors.append("nofollow")
     except Exception as e:errors.append(repr(e))
     finally:await ctx.close()
     result={"engine":engine,"page":file,"width":w,"errors":errors}
     results.append(result)
     if errors:print("CATEGORY BROWSER ISSUE",json.dumps(result),flush=True)
   await asyncio.gather(*(test(f,w,h) for f in PAGES for w,h in [(390,844),(1440,900)]))
   await browser.close()
 report={"expected":96,"completed":len(results),"passed":sum(not x["errors"] for x in results),"results":results,"static":rows}
 out=P("qa-report");out.mkdir(exist_ok=True)
 (out/"category-hubs.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print("CATEGORY BROWSER",json.dumps({k:v for k,v in report.items() if k not in ("results","static")}),flush=True)
 assert report["passed"]==96
asyncio.run(browser_checks())
