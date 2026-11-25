import asyncio,json,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit
from playwright.async_api import async_playwright
from outbound_nofollow import external
PAGES=["about.htm","damerau-levenshtein-distance.html","levenshtein-vs-damerau-and-hamming.html","indexing-and-filtering-for-edit-distance.html","edit-distance-in-genomic-search-and-read-mapping.html","insertion-deletion-codes-and-synchronization-errors.html","name-address-and-place-matching.html"]
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  p=super().translate_path(path)
  if not Path(p).exists() and Path(p+".html").is_file():return p+".html"
  return p
 def log_message(self,*args):pass
server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
origin="http://127.0.0.1:"+str(server.server_port)
async def main():
 rows=[]
 async with async_playwright() as pw:
  for name in ["chromium","firefox","webkit"]:
   browser=await getattr(pw,name).launch()
   for file in PAGES:
    for w,h in [(390,844),(1440,900)]:
     errors=[];ctx=await browser.new_context(viewport={"width":w,"height":h})
     try:
      page=await ctx.new_page()
      page.on("pageerror",lambda e:errors.append(str(e)))
      await ctx.route("**/*",lambda r:r.continue_() if r.request.url.startswith(origin+"/") else r.abort())
      res=await page.goto(origin+"/"+file,wait_until="domcontentloaded",timeout=20000)
      await page.evaluate("Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,1000))])")
      data=await page.evaluate("""() => ({width:document.documentElement.scrollWidth,viewport:innerWidth,links:[...document.querySelectorAll('a[href],area[href]')].map(e=>({href:e.getAttribute('href'),rel:e.getAttribute('rel')||''})),h1:document.querySelectorAll('h1').length})""")
      if not res or res.status!=200:errors.append("HTTP")
      if data["width"]>w+2:errors.append("horizontal overflow")
      if data["h1"]!=1:errors.append("h1 count")
      if any(external(a["href"] or "") and "nofollow" not in a["rel"].lower().split() for a in data["links"]):errors.append("missing nofollow")
     except Exception as e:errors.append(repr(e))
     finally:await ctx.close()
     row={"page":file,"engine":name,"width":w,"errors":errors};rows.append(row);print(json.dumps(row),flush=True)
   await browser.close()
 out=Path("qa-report");out.mkdir(exist_ok=True)
 report={"expected":42,"completed":len(rows),"passed":sum(not x["errors"] for x in rows),"results":rows}
 (out/"final-delta.json").write_text(json.dumps(report,indent=2));print("DELTA SUMMARY",json.dumps({k:v for k,v in report.items() if k!="results"}))
 if report["passed"]!=42:raise SystemExit(1)
asyncio.run(main())
