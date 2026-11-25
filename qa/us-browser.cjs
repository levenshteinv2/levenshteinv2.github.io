const {chromium}=require('playwright');
const http=require('node:http'), fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
const server=http.createServer((req,res)=>{let p=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(p==='/fancy-text-generator')p+='.html';if(p==='/')p='/index.html';const f=path.resolve('.'+p);if(!f.startsWith(process.cwd()+path.sep)||!fs.existsSync(f)){res.writeHead(404);return res.end('Not found')}res.setHeader('Content-Type',f.endsWith('.js')?'application/javascript; charset=utf-8':'text/html; charset=utf-8');res.end(fs.readFileSync(f))});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const base='http://127.0.0.1:'+server.address().port;
const ctx=await browser.newContext({viewport:{width:1280,height:900},permissions:['clipboard-read','clipboard-write'],acceptDownloads:true});
const page=await ctx.newPage(), failures=[],results=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
const test=async(name,fn)=>{try{await fn();results.push({name,status:'PASS'});console.log('PASS '+name)}catch(e){failures.push(name);results.push({name,status:'FAIL',detail:String(e).slice(0,250)});console.log('FAIL '+name+': '+String(e).slice(0,250))}};
const sel=s=>page.locator(s), tab=async(name)=>{await page.locator('[data-tab]').filter({hasText:name}).first().click({timeout:3000})};
const visible=async s=>{await sel(s).waitFor({state:'visible',timeout:4000})};
const download=async s=>{const [d]=await Promise.all([page.waitForEvent('download',{timeout:12000}),sel(s).click({timeout:4000})]);const bytes=fs.readFileSync(await d.path());assert(bytes.length>100);return {filename:d.suggestedFilename(),bytes}};
const start=async()=>{await page.goto(base+'/fancy-text-generator',{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.querySelectorAll('#quick-grid .lf-font-item').length>200,{},{timeout:10000})};
try{
await test('exact source renders quick grid',async()=>{await start();assert.equal(await page.locator('html').getAttribute('lang'),'en-US');assert.equal(await page.locator('h1').count(),1);assert.equal(await page.locator('#quick-grid .lf-font-item').count(),316)});
await test('quick transformation and clipboard',async()=>{await sel('#quick-input').fill('Hello USA');const card=sel('#quick-grid .lf-font-item').first();const value=await card.locator('.lf-font-styled').innerText();assert(value&&value!=='Hello USA');await card.click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),value)});
await test('quick Unicode input',async()=>{await sel('#quick-input').fill('Cafe\u0301 👩‍💻');const val=await sel('#quick-grid .lf-font-item .lf-font-styled').first().innerText();assert(val.includes('👩‍💻'))});
await test('aesthetic generation',async()=>{await sel('#fsd-aesthetic-generate').click();await visible('#fsd-aesthetic-result');assert((await sel('#fsd-aesthetic-output').innerText()).trim().length>0)});
await test('aesthetic handoff',async()=>{await sel('#fsd-aesthetic-handoff').selectOption('writer');await visible('#tw-editor');assert((await sel('#tw-editor').inputValue()).length>0)});
await test('writer input and undo/redo',async()=>{await visible('#tw-editor');await sel('#tw-editor').fill('First');await sel('#tw-editor').press('End');await sel('#tw-editor').pressSequentially(' second',{delay:70});const final=await sel('#tw-editor').inputValue();await sel('#tw-btn-undo').click();assert.notEqual(await sel('#tw-editor').inputValue(),final);await sel('#tw-btn-redo').click();assert.equal(await sel('#tw-editor').inputValue(),final)});
await test('writer font modal',async()=>{await sel('#tw-btn-fonts').click();await visible('#tw-fonts-modal');assert((await sel('#tw-fonts-grid').innerText()).length>10);await sel('#tw-fonts-close').click()});
await test('writer symbol picker',async()=>{await sel('#tw-btn-symbols').click();await visible('#tw-symbols-modal');assert((await sel('#tw-symbols-grid').innerText()).length>0);await sel('#tw-symbols-close').click()});
await test('TXT import',async()=>{await sel('#tw-btn-more').click();await sel('#tw-btn-upload').click();await sel('#tw-file-input').setInputFiles({name:'sample.txt',mimeType:'text/plain',buffer:Buffer.from('Hello from QA fixture')});await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('Hello from QA fixture'),{},{timeout:5000})});
await test('PNG export actual download',async()=>{await sel('#tw-editor').fill('Hello QA');await sel('#tw-btn-save-image').click();await visible('#tw-export-modal');await sel('#tw-btn-export-download').click();await visible('#tw-result-modal');const d=await download('#tw-result-download');assert.equal(d.bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');await sel('#tw-result-close').click()});
await test('long text DOCX export actual download',async()=>{await sel('#tw-editor').fill(('Long text from USA QA. '.repeat(45)+'\n').repeat(10));await sel('#tw-btn-save-image').click();await visible('#tw-long-export-panel');const d=await download('#tw-btn-export-docx');assert.equal(d.bytes.subarray(0,2).toString(),'PK');assert(d.filename.endsWith('.docx'));await sel('#tw-export-close').click()});
await test('bio preview updates',async()=>{await start();await tab('Bio');await sel('#bio-input').fill('Alex | NYC');assert((await sel('#bio-preview').innerText()).includes('Alex'));await sel('#bio-copy').click();assert((await page.evaluate(()=>navigator.clipboard.readText())).includes('Alex'))});
await test('game name and matrix',async()=>{await tab('Game');await sel('#lf194-input').fill('Alex');await sel('#lf194-btn-random').click();assert((await sel('#lf194-preview').innerText()).trim().length>0);await sel('#lf194-btn-matrix').click();await visible('#lf194-matrix-wrap');assert((await sel('#lf194-matrix').innerText()).length>0)});
await test('certificate image',async()=>{await sel('#lf194-btn-cert').click();await visible('#lf194-cert-modal');const d=await download('#lf194-cert-dl');assert.equal(d.bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a');await sel('#lf194-cert-close').click()});
await test('no uncaught page errors',async()=>assert.deepEqual(errors,[]));
for(const width of [360,390,768])await test('mobile width '+width,async()=>{const c=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});try{const p=await c.newPage();await p.goto(base+'/fancy-text-generator');await p.waitForSelector('#quick-grid .lf-font-item');assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));}finally{await c.close()}});
await test('live URL and source revision',async()=>{const r=await fetch('https://levenshteinv2.github.io/fancy-text-generator',{redirect:'follow'});assert.equal(r.status,200);assert.equal(new URL(r.url).host,'levenshteinv2.github.io');const html=await r.text();assert(html.includes('text-writer-us3.js'));assert(html.includes('https://www.levenshtein.net/fancy-text-generator'));assert(html.includes('>Clear</button>'))});
console.log('QA_JSON '+JSON.stringify({results,errors}));
}finally{await browser.close();server.close()}
if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
