import asyncio,json,os,re,threading
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
P=Path('.github/qa/pages.json')
pages=json.loads(P.read_text())
assert len(pages)==91 and len(set(pages))==91
out=Path('qa-report');out.mkdir(exist_ok=True)
issues=[]; results=[]
def issue(page,kind,detail): issues.append(dict(page=page,kind=kind,detail=detail))
class Handler(SimpleHTTPRequestHandler):
 def translate_path(self,path):
  p=super().translate_path(path)
  if not os.path.exists(p) and os.path.isfile(p+'.html'): return p+'.html'
  return p
 def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
origin='http://127.0.0.1:'+str(server.server_port)
for name in pages:
 p=Path(name)
 if not p.is_file(): issue(name,'missing','file');continue
 s=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
 for selector in ['title','meta[name=description]','meta[name=viewport]','link[rel=canonical]','h1','main']:
  n=len(s.select(selector))
  if n!=1: issue(name,'markup',selector+': '+str(n))
 for tag in s.select('meta[content]'):
  if 'null.gif' in tag.get('content',''): issue(name,'metadata','null.gif')
 for a in s.select('a[href]'):
  h=a['href'];u=urlsplit(h)
  if u.scheme or u.netloc: continue
  dest=Path(unquote(u.path.lstrip('/'))) if u.path.startswith('/') else p.parent/unquote(u.path) if u.path else p
  candidates=[dest,Path(str(dest)+'.html'),dest/'index.html']
  if not any(x.is_file() for x in candidates): issue(name,'link',h)
 for tag in s.select('script[type="application/ld+json"]'):
  try: json.loads(tag.get_text())
  except Exception: issue(name,'schema','invalid JSON')
async def run():
 async with async_playwright() as pw:
  for engine,sizes in [('chromium',[(320,568),(375,667),(390,844),(430,932),(768,1024),(1024,768),(1440,900)]),('firefox',[(390,844),(1440,900)]),('webkit',[(390,844),(1440,900)])]:
   browser=await getattr(pw,engine).launch()
   sem=asyncio.Semaphore(5)
   async def check(name,w,h):
    async with sem:
     context=await browser.new_context(viewport={'width':w,'height':h})
     page=await context.new_page()
     errors=[]
     page.on('pageerror',lambda e:errors.append(str(e)))
     try:
      response=await page.goto(origin+'/'+name,wait_until='domcontentloaded',timeout=15000)
      await page.evaluate('document.fonts.ready')
      data=await page.evaluate("""() => ({width:document.documentElement.scrollWidth,viewport:innerWidth,overflow:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0 && r.right>innerWidth+2 && !e.closest('.ux-scroll')}).slice(0,8).map(e=>e.tagName+'.'+String(e.className).slice(0,80))})""")
      failures=[]
      if not response or response.status!=200: failures.append('HTTP '+str(response.status if response else None))
      if data['width']>w+2: failures.append('horizontal overflow '+str(data))
      failures+=errors
      for f in failures: issue(name,engine+' '+str(w),f)
      if failures and len(list(out.glob('*.png')))<40: await page.screenshot(path=str(out/(name+'-'+engine+'-'+str(w)+'.png')),timeout=5000)
      results.append(dict(page=name,engine=engine,width=w,passed=not failures))
     except Exception as e:
      issue(name,engine+' '+str(w),str(e));results.append(dict(page=name,engine=engine,width=w,passed=False))
     finally: await context.close()
   await asyncio.gather(*(check(n,w,h) for n in pages for w,h in sizes))
   await browser.close()
try: asyncio.run(run())
finally:
 report=dict(pages=len(pages),expected_browser_checks=len(pages)*11,completed=len(results),passed=sum(r['passed'] for r in results),issues=issues,results=results)
 (out/'report.json').write_text(json.dumps(report,indent=2))
 summary={k:v for k,v in report.items() if k not in ('issues','results')}
 print('QA SUMMARY',json.dumps(summary), 'issues',len(issues))
 for i in issues[:100]: print('QA ISSUE',json.dumps(i))
 if os.getenv('GITHUB_STEP_SUMMARY'):
  with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f: f.write('## V2 QA\\n'+str(summary)+'\\nIssues: '+str(len(issues)))
if issues or len(results)!=len(pages)*11: raise SystemExit(1)
