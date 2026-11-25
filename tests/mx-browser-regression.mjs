import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root=process.cwd(), tmp=await mkdtemp(path.join(tmpdir(),'mx-qa-'));
const server=createServer(async (req,res)=>{
  let pathname=new URL(req.url,'http://127.0.0.1').pathname;
  if(pathname==='/letras-bonitas')pathname+='.html';
  try{const file=path.resolve(root,'.'+pathname);if(!file.startsWith(root+path.sep))throw Error('path');
    const data=await readFile(file);res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript; charset=utf-8':'text/html; charset=utf-8');res.end(data);
  }catch{res.statusCode=404;res.end('not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true});
const errors=[],results=[];
const context=await browser.newContext({acceptDownloads:true,viewport:{width:1280,height:900},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();
page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/*',route=>route.request().url().startsWith(origin)||route.request().url().startsWith('data:')?route.continue():route.abort());
const loc=id=>page.locator('#'+id);
async function fresh(){await page.goto(origin+'/letras-bonitas');await page.waitForFunction(()=>document.querySelectorAll('#quick-grid .lf-font-item').length===316);await page.evaluate(()=>localStorage.clear());}
async function tab(name){await page.locator('[data-tab="'+name+'"]').click();}
async function test(name,fn){try{await fresh();await fn();results.push({name,status:'PASS'});console.log('PASS '+name);}catch(e){results.push({name,status:'FAIL',error:String(e)});console.error('FAIL '+name+' '+e);}}
const delay=()=>page.waitForTimeout(350);
async function download(click,name){const p=page.waitForEvent('download',{timeout:12000});await click();const d=await p;const file=path.join(tmp,name);await d.saveAs(file);assert.equal(await d.failure(),null);return file;}
async function openExport(text,mode='social'){await tab('writer');await loc('tw-editor').fill(text);await loc('tw-btn-save-image').click();await page.locator('[data-export-mode="'+mode+'"]').click();await delay();}
const long=Array.from({length:55},(_,i)=>'Línea '+(i+1)+' — José, niño y pingüino.').join('\n');
await test('metadata, 316 styles, accents, clipboard',async()=>{
 assert.equal(await page.locator('html').getAttribute('lang'),'es-MX');
 assert.equal(await page.locator('h1').count(),1);
 assert.equal(await page.locator('h1').innerText(),'Letras Bonitas');
 await loc('quick-input').fill('José, niño, pingüino');await delay();
 let styles=await page.locator('#quick-grid .lf-font-styled').allTextContents();assert.equal(styles.length,316);
 assert(styles.every(s=>s.normalize('NFKD').includes('\u0303')&&s.normalize('NFKD').includes('\u0308')&&s.normalize('NFKD').includes('\u0301')));
 await page.locator('#quick-grid .lf-font-item').first().click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),styles[0]);
 await loc('quick-input').fill('Copy');await delay();assert((await page.locator('#quick-grid .lf-font-styled').allTextContents()).some(x=>x.includes('Copy')));
});
await test('aesthetic generation and handoff',async()=>{
 await loc('quick-input').fill('México QA');await loc('fsd-aesthetic-generate').click();await delay();
 let output=await loc('fsd-aesthetic-output').innerText();assert(output.trim().length>0);
 await loc('fsd-aesthetic-handoff').selectOption('writer');await delay();assert.equal(await loc('tw-editor').inputValue(),output);
});
await test('bio literal text and clear',async()=>{
 await tab('bio');await loc('bio-input').fill('Copy');await delay();assert.equal((await loc('bio-preview').innerText()).trim(),'Copy');
 await loc('bio-copy').click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'Copy');
 await loc('bio-clear').click();await delay();assert.equal(await loc('bio-input').inputValue(),'');
});
await test('editor history, grapheme-safe selection, symbol insertion',async()=>{
 await tab('writer');let e=loc('tw-editor');await e.fill('José niño');await delay();await loc('tw-btn-undo').click();assert.notEqual(await e.inputValue(),'José niño');await loc('tw-btn-redo').click();assert.equal(await e.inputValue(),'José niño');
 await e.evaluate(n=>{n.focus();n.setSelectionRange(0,4);n.dispatchEvent(new Event('select'));});await loc('tw-btn-more').click();await loc('tw-us-upper').click();assert.equal(await e.inputValue(),'JOSÉ niño');
 await loc('tw-btn-symbols').click();await page.locator('#tw-symbols-grid button').first().click();assert.notEqual(await e.inputValue(),'JOSÉ niño');
});
await test('name random, matrix, certificate file',async()=>{
 await tab('pro');await loc('lf194-input').fill('José');await delay();let before=await loc('lf194-preview').innerText();await loc('lf194-btn-random').click();await delay();assert.notEqual(await loc('lf194-preview').innerText(),before);
 assert.match(await loc('lf194-b-blacklist').innerText(),/no verificada/);
 await loc('lf194-btn-matrix').click();assert(await page.locator('#lf194-matrix table').isVisible());
 await loc('lf194-btn-cert').click();await delay();assert(await loc('lf194-cert-modal').isVisible());let f=await download(()=>loc('lf194-cert-dl').click(),'certificate.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('PNG actual download',async()=>{
 await openExport('José, niño, pingüino');await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'social.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('handwriting PNG actual download',async()=>{
 await openExport('José, niño, pingüino','handwriting');await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'handwriting.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('multi-page styled PDF actual download',async()=>{
 await openExport(long);await loc('tw-long-export-panel').waitFor({state:'visible'});await loc('tw-btn-export-styled-pdf').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'styled.pdf');assert.equal((await readFile(f)).subarray(0,4).toString(),'%PDF');
});
await test('multi-page DOCX export and reimport',async()=>{
 await openExport(long);await loc('tw-long-export-panel').waitFor({state:'visible'});let f=await download(()=>loc('tw-btn-export-docx').click(),'doc.docx');let xml=execFileSync('unzip',['-p',f,'word/document.xml'],{encoding:'utf8'});assert(xml.includes('José, niño y pingüino.'));
 await loc('tw-export-close').click();await loc('tw-editor').fill('');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles(f);await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('Línea 55'));
});
await test('carousel ZIP actual download',async()=>{
 await openExport(long);await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});await loc('tw-result-more').click();let f=await download(()=>loc('tw-result-download-all').click(),'carousel.zip');let entries=execFileSync('unzip',['-Z1',f],{encoding:'utf8'}).trim().split('\n');assert(entries.filter(x=>x.endsWith('.png')).length>1);
});
await test('TXT import actual content',async()=>{
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.txt',mimeType:'text/plain',buffer:Buffer.from('José, niño, pingüino')});await page.waitForFunction(()=>document.querySelector('#tw-editor').value==='José, niño, pingüino');
});
for(const width of [320,375,390,430])await test('mobile layout '+width,async()=>{
 await page.setViewportSize({width,height:844});await delay();
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 let tabs=await page.locator('.lf-tab').evaluateAll(ns=>ns.map(n=>({left:n.getBoundingClientRect().left,right:n.getBoundingClientRect().right,width:n.getBoundingClientRect().width})));assert.equal(tabs.length,4);assert(tabs.every(x=>x.width>0&&x.left>=0&&x.right<=width+1));
 await tab('writer');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));await page.setViewportSize({width:1280,height:900});
});

await test('SEO, lazy asset, original market, symbols',async()=>{
 assert.equal(await page.title(),'Letras Bonitas para Copiar y Pegar | Levenshtein.net');
 assert.equal(await page.locator('link[rel=canonical]').getAttribute('href'),'https://www.levenshtein.net/letras-bonitas');
 assert.match(await page.locator('meta[name=robots]').getAttribute('content'),/noindex/);
 let graph=JSON.parse(await page.locator('script[type="application/ld+json"]').textContent());assert.equal(graph['@graph'].length,6);
 assert.equal(await page.evaluate(()=>window.FSDMarketFonts.market),'es-bonitas');
 assert.equal(await page.evaluate(()=>typeof window.JSZip),'undefined');
 await tab('writer');await loc('tw-btn-symbols').click();assert((await page.locator('#tw-symbols-grid button').count())>0);
});
await test('Markdown import and persistence',async()=>{
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.md',mimeType:'text/markdown',buffer:Buffer.from('# Niño\n**José**')});await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('José'));await delay();await page.reload();await tab('writer');assert((await loc('tw-editor').inputValue()).includes('José'));
});
await test('keyboard focus and mobile tap targets',async()=>{
 await page.setViewportSize({width:390,height:844});await tab('writer');await loc('tw-editor').focus();assert.equal(await page.evaluate(()=>document.activeElement.id),'tw-editor');assert(await loc('tw-editor').evaluate(n=>parseFloat(getComputedStyle(n).fontSize)>=16));await page.setViewportSize({width:1280,height:900});
});


await test('PDF text-layer import',async()=>{
 const stream='BT /F1 12 Tf 72 720 Td (Mexico PDF import test) Tj ET';
 const objs=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>','<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>','<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>','<< /Length '+stream.length+' >>\nstream\n'+stream+'\nendstream'];
 let pdf='%PDF-1.4\n',offs=[0];for(let i=0;i<objs.length;i++){offs.push(Buffer.byteLength(pdf));pdf+=(i+1)+' 0 obj\n'+objs[i]+'\nendobj\n';}let xref=Buffer.byteLength(pdf);pdf+='xref\n0 6\n0000000000 65535 f \n'+offs.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+xref+'\n%%EOF\n';
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.pdf',mimeType:'application/pdf',buffer:Buffer.from(pdf)});await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('Mexico PDF import test'),{},{timeout:10000});
});
await test('local payload and interaction timing',async()=>{
 const metrics=await page.evaluate(()=>{const nav=performance.getEntriesByType('navigation')[0];const rs=performance.getEntriesByType('resource').filter(x=>x.name.startsWith(location.origin));return {domContentLoadedMs:Math.round(nav.domContentLoadedEventEnd),loadMs:Math.round(nav.loadEventEnd),localEncodedBytes:nav.encodedBodySize+rs.reduce((a,x)=>a+x.encodedBodySize,0),localRequests:rs.length+1};});
 console.log('MX_LAB_METRICS '+JSON.stringify(metrics));
 assert(metrics.localEncodedBytes>0);assert(metrics.localRequests>=5);assert(!await page.evaluate(()=>performance.getEntriesByType('resource').some(x=>x.name.includes('jszip'))));
});

console.log('MX_QA_RESULT '+JSON.stringify({results,pageErrors:errors}));
await browser.close();server.close();
if(results.some(x=>x.status==='FAIL')||errors.length)process.exitCode=1;
