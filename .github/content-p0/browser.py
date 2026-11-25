import asyncio,json,threading,os
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.async_api import async_playwright
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  p=super().translate_path(path)
  return p+'.html' if not os.path.exists(p) and os.path.isfile(p+'.html') else p
 def log_message(self,*a):pass
srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=srv.serve_forever,daemon=True).start()
origin='http://127.0.0.1:'+str(srv.server_port)
async def main():
 out=[];errors=[]
 async with async_playwright() as pw:
  b=await pw.chromium.launch()
  sem=asyncio.Semaphore(4)
  async def test(p,w,h):
   async with sem:
    ctx=await b.new_context(viewport={'width':w,'height':h})
    await ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin+'/') else r.abort())
    page=await ctx.new_page();err=[]
    page.on('pageerror',lambda e:err.append(str(e)))
    try:
     r=await page.goto(origin+'/'+p,wait_until='domcontentloaded',timeout=12000)
     data=await page.evaluate("""() => ({width:document.documentElement.scrollWidth,viewport:innerWidth,related:[...document.querySelectorAll('h2.lv-related-title + ol.lv-posts li.lv-post h3 a')].map(x=>x.getAttribute('href'))})""")
     route='/'+p.removesuffix('.html') if p!='index.html' else '/'
     assert r and r.status==200 and data['width']<=w+2 and route not in data['related'] and not err,(data,err)
     out.append(dict(path=p,width=w,passed=True))
    except Exception as e:
     errors.append(dict(path=p,width=w,error=str(e)));out.append(dict(path=p,width=w,passed=False))
    finally:await ctx.close()
  paths=['index.html','ukkonen-algorithm.html','translation-edit-rate-and-mt-evaluation.html','damerau-levenshtein-distance.html','string-metrics.html','paper-levenshtein-1966.html']
  await asyncio.gather(*(test(p,w,h) for p in paths for w,h in [(390,844),(1366,900)]))
  await b.close()
 report=dict(checks=len(out),passed=sum(x['passed'] for x in out),errors=errors,results=out,scope='Local staging HTTP, Chromium 390 and 1366; external requests blocked; no live Preview test')
 Path('.github/content-p0/browser-results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report));assert len(out)==12 and not errors
asyncio.run(main())
