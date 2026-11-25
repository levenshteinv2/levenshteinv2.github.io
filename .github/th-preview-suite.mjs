import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root=path.resolve(process.argv[2]), tmp=path.resolve(process.argv[3]);
await mkdir(tmp,{recursive:true});
const server=createServer(async (req,res)=>{
  let pathname=new URL(req.url,'http://127.0.0.1').pathname;
  if(pathname==='/akson-phiset')pathname+='.html';
  try{const file=path.resolve(root,'.'+pathname);if(!file.startsWith(root+path.sep))throw Error('path');
    const data=await readFile(file);res.setHeader('Content-Type',file.endsWith('.js')?'text/javascript; charset=utf-8':file.endsWith('.ttf')?'font/ttf':file.endsWith('.woff2')?'font/woff2':'text/html; charset=utf-8');res.end(data);
  }catch{res.statusCode=404;res.end('not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=process.env.QA_ORIGIN || 'http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN});
const errors=[],results=[];
const context=await browser.newContext({acceptDownloads:true,viewport:{width:1280,height:900},permissions:['clipboard-read','clipboard-write']});
const page=await context.newPage();page.setDefaultTimeout(6500);
page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/*',route=>route.request().url().startsWith(origin)||route.request().url().startsWith('data:')?route.continue():route.abort());
const loc=id=>page.locator('#'+id);
async function fresh(){await page.goto(origin+'/akson-phiset');await page.evaluate(()=>localStorage.clear());await page.reload();await page.waitForFunction(()=>document.querySelectorAll('#quick-grid .lf-font-item').length===325);}
async function tab(name){await page.locator('[data-tab="'+name+'"]').click();}
async function test(name,fn){try{await fresh();await tab('quick');await fn();results.push({name,status:'PASS'});console.log('PASS '+name);}catch(e){results.push({name,status:'FAIL',error:String(e)});console.error('FAIL '+name+' '+e);}}
const delay=()=>page.waitForTimeout(350);
async function download(click,name){const [d]=await Promise.all([page.waitForEvent('download',{timeout:15000}),click()]);const file=path.join(tmp,name);await d.saveAs(file);assert.equal(await d.failure(),null);return file;}
async function openExport(text,mode='social'){await tab('writer');await loc('tw-editor').fill(text);await loc('tw-btn-save-image').click();await page.locator('[data-export-mode="'+mode+'"]').click();await delay();}
const long=Array.from({length:55},(_,i)=>'บรรทัด '+(i+1)+' — สวัสดีครับ น้ำ ก้ ๑๒๓').join('\n');
await test('metadata, 325 styles, Thai preservation, clipboard',async()=>{
 assert.equal(await page.locator('html').getAttribute('lang'),'th-TH');
 assert.equal(await page.locator('h1').count(),1);
 assert.equal(await page.locator('h1').innerText(),'อักษรพิเศษ');
 await loc('quick-input').fill('สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻');await delay();
 let styles=await page.locator('#quick-grid .lf-font-styled').allTextContents();assert.equal(styles.length,325);
 const nativeRows=await page.evaluate(()=>document.querySelector('#quick-grid').__fsdFontCards.map(c=>({name:c.f.name,id:c.f.fsdMarketId||'',out:c.styledEl.textContent})));
 assert(nativeRows.every(x=>x.out.length>0));assert(nativeRows.some(x=>x.out.includes('สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻')));
 await page.locator('#quick-grid .lf-font-item').first().click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),styles[0]);
 await loc('quick-input').fill('Copy');await delay();assert((await page.locator('#quick-grid .lf-font-styled').allTextContents()).some(x=>x.includes('Copy')));
});
await test('aesthetic generation and handoff',async()=>{
 await loc('quick-input').fill('สวัสดีครับ น้ำ');await loc('fsd-aesthetic-generate').click();await delay();
 let output=await loc('fsd-aesthetic-output').innerText();assert(output.trim().length>0);
 await loc('fsd-aesthetic-handoff').selectOption('writer');await delay();assert.equal(await loc('tw-editor').inputValue(),output);
});
await test('bio literal text and clear',async()=>{
 await tab('bio');await loc('bio-input').fill('Copy');await delay();assert.equal((await loc('bio-preview').innerText()).trim(),'Copy');
 await loc('bio-copy').click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),'Copy');
 await loc('bio-clear').click();await delay();assert.equal(await loc('bio-input').inputValue(),'');
});
await test('editor history, selection and symbol insertion',async()=>{
 await tab('writer');let e=loc('tw-editor');await e.fill('ก่อน abc น้ำ หลัง');await delay();await loc('tw-btn-undo').click();assert.notEqual(await e.inputValue(),'ก่อน abc น้ำ หลัง');await loc('tw-btn-redo').click();assert.equal(await e.inputValue(),'ก่อน abc น้ำ หลัง');
 await e.evaluate(n=>{n.focus();n.setSelectionRange(5,8);n.dispatchEvent(new Event('select'));});if(!await loc('tw-us-upper').isVisible())await loc('tw-btn-more').click();await loc('tw-us-upper').click();assert.equal(await e.inputValue(),'ก่อน ABC น้ำ หลัง');
 await loc('tw-btn-symbols').click();await page.locator('#tw-symbols-grid button').first().click();assert.notEqual(await e.inputValue(),'ก่อน ABC น้ำ หลัง');
});
await test('name random, matrix, certificate file',async()=>{
 await tab('pro');await loc('lf194-input').fill('สวัสดีครับ');await delay();let before=await loc('lf194-preview').innerText();await loc('lf194-btn-random').click();await delay();assert.notEqual(await loc('lf194-preview').innerText(),before);
 assert.match(await loc('lf194-b-blacklist').innerText(),/ยังไม่ได้ตรวจสอบ/);
 await loc('lf194-btn-matrix').click();assert(await page.locator('#lf194-matrix table').isVisible());const target=await loc('lf194-preview').innerText();const source=await loc('lf194-input').inputValue();const mat=await page.locator('#lf194-matrix tbody tr').evaluateAll(ns=>ns.map(n=>[...n.querySelectorAll('td')].map(c=>Number(c.textContent))));assert.equal(mat.length,source.length+1);for(let i=0;i<=source.length;i++){assert.equal(mat[i].length,target.length+1);for(let j=0;j<=target.length;j++){const expect=i===0?j:j===0?i:Math.min(mat[i-1][j]+1,mat[i][j-1]+1,mat[i-1][j-1]+Number(source[i-1]!==target[j-1]));assert.equal(mat[i][j],expect);}}
 await loc('lf194-btn-cert').click();await delay();assert(await loc('lf194-cert-modal').isVisible());let f=await download(()=>loc('lf194-cert-dl').click(),'certificate.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('PNG actual download',async()=>{
 await openExport('สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻');await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'social.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('handwriting PNG actual download',async()=>{
 await openExport('สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻','handwriting');await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'handwriting.png');assert.equal((await readFile(f)).subarray(0,8).toString('hex'),'89504e470d0a1a0a');
});
await test('handwriting PDF download',async()=>{await openExport(long,'handwriting');await loc('tw-btn-export-pdf').click();await loc('tw-result-modal').waitFor({state:'visible'});const f=await download(()=>loc('tw-result-download').click(),'handwriting.pdf');assert.equal((await readFile(f)).subarray(0,4).toString(),'%PDF');});
await test('multi-page styled PDF actual download',async()=>{
 await openExport(long);await loc('tw-long-export-panel').waitFor({state:'visible'});await loc('tw-btn-export-styled-pdf').click();await loc('tw-result-modal').waitFor({state:'visible'});let f=await download(()=>loc('tw-result-download').click(),'styled.pdf');assert.equal((await readFile(f)).subarray(0,4).toString(),'%PDF');
});
await test('multi-page DOCX export and reimport',async()=>{
 await openExport(long);await loc('tw-long-export-panel').waitFor({state:'visible'});let f=await download(()=>loc('tw-btn-export-docx').click(),'doc.docx');let xml=execFileSync(process.env.QA_PYTHON||'python',['-X','utf8','-c',"import sys,zipfile;sys.stdout.buffer.write(zipfile.ZipFile(sys.argv[1]).read('word/document.xml'))",f],{encoding:'utf8'});assert(xml.includes('สวัสดีครับ น้ำ ก้ ๑๒๓'));
 await loc('tw-export-close').click();await loc('tw-editor').fill('');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles(f);await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('บรรทัด 55'));
});
await test('carousel ZIP actual download',async()=>{
 await openExport(long);await loc('tw-btn-export-download').click();await loc('tw-result-modal').waitFor({state:'visible'});await loc('tw-result-more').click();let f=await download(()=>loc('tw-result-download-all').click(),'carousel.zip');let entries=JSON.parse(execFileSync(process.env.QA_PYTHON||'python',['-c',"import sys,zipfile,json;print(json.dumps(zipfile.ZipFile(sys.argv[1]).namelist()))",f],{encoding:'utf8'}));assert(entries.filter(x=>x.endsWith('.png')).length>1);
});
await test('TXT import actual content',async()=>{
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.txt',mimeType:'text/plain',buffer:Buffer.from('สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻')});await page.waitForFunction(()=>document.querySelector('#tw-editor').value==='สวัสดีครับ น้ำ ก้ ๑๒๓ 👩‍💻');
});
for(const width of [320,375,390,430])await test('mobile layout '+width,async()=>{
 await page.setViewportSize({width,height:844});await delay();await page.screenshot({path:path.join(tmp,'width-'+width+'.png')});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 let tabs=await page.locator('.lf-tab').evaluateAll(ns=>ns.map(n=>({left:n.getBoundingClientRect().left,right:n.getBoundingClientRect().right,width:n.getBoundingClientRect().width})));assert.equal(tabs.length,4);assert(tabs.every(x=>x.width>0&&x.left>=0&&x.right<=width+1));
 await tab('writer');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));await page.setViewportSize({width:1280,height:900});
});

await test('SEO, market, symbols',async()=>{
 assert.equal(await page.title(),'อักษรพิเศษ – ตัวอักษรพิเศษและสัญลักษณ์ | Levenshtein.net');
 assert.equal(await page.locator('link[rel=canonical]').getAttribute('href'),'https://www.levenshtein.net/akson-phiset');
 assert.match(await page.locator('meta[name=robots]').getAttribute('content'),/noindex/);
 let graph=JSON.parse(await page.locator('script[type="application/ld+json"]').textContent());assert(graph['@graph'].some(n=>n['@type']==='WebApplication'&&n.inLanguage==='th-TH'));
 assert.equal(await page.evaluate(()=>window.FSDMarketFonts.market),'th');
 assert.equal(await page.locator('meta[name=fsd-market]').getAttribute('content'),'th');
 await tab('writer');await loc('tw-btn-symbols').click();assert((await page.locator('#tw-symbols-grid button').count())>0);
});
await test('Markdown import and persistence',async()=>{
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.md',mimeType:'text/markdown',buffer:Buffer.from('## น้ำ\n**สวัสดีครับ**')});await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('สวัสดีครับ'));await delay();await page.reload();await tab('writer');assert((await loc('tw-editor').inputValue()).includes('สวัสดีครับ'));
});
await test('keyboard focus and mobile tap targets',async()=>{
 await page.setViewportSize({width:390,height:844});await tab('writer');await loc('tw-editor').focus();assert.equal(await page.evaluate(()=>document.activeElement.id),'tw-editor');assert(await loc('tw-editor').evaluate(n=>parseFloat(getComputedStyle(n).fontSize)>=16));await page.setViewportSize({width:1280,height:900});
});


await test('PDF text-layer import',async()=>{
 const stream='BT /F1 12 Tf 72 720 Td (Hamburg PDF Import) Tj ET';
 const objs=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R] /Count 1 >>','<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>','<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>','<< /Length '+stream.length+' >>\nstream\n'+stream+'\nendstream'];
 let pdf='%PDF-1.4\n',offs=[0];for(let i=0;i<objs.length;i++){offs.push(Buffer.byteLength(pdf));pdf+=(i+1)+' 0 obj\n'+objs[i]+'\nendobj\n';}let xref=Buffer.byteLength(pdf);pdf+='xref\n0 6\n0000000000 65535 f \n'+offs.slice(1).map(n=>String(n).padStart(10,'0')+' 00000 n \n').join('')+'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+xref+'\n%%EOF\n';
 await tab('writer');await loc('tw-btn-more').click();await loc('tw-btn-upload').click();await loc('tw-file-input').setInputFiles({name:'sample.pdf',mimeType:'application/pdf',buffer:Buffer.from(pdf)});await page.waitForFunction(()=>document.querySelector('#tw-editor').value.includes('Hamburg PDF Import'),{},{timeout:10000});
});
await test('local payload and interaction timing',async()=>{
 const metrics=await page.evaluate(()=>{const nav=performance.getEntriesByType('navigation')[0];const rs=performance.getEntriesByType('resource').filter(x=>x.name.startsWith(location.origin));return {domContentLoadedMs:Math.round(nav.domContentLoadedEventEnd),loadMs:Math.round(nav.loadEventEnd),localEncodedBytes:nav.encodedBodySize+rs.reduce((a,x)=>a+x.encodedBodySize,0),localRequests:rs.length+1};});
 console.log('TH_LAB_METRICS '+JSON.stringify(metrics));
 assert(metrics.localEncodedBytes>0);assert(metrics.localRequests>=1);
});


for(const [key,input,start,end,want] of [
 ['lower','น้ำ ABC ก้',4,7,'น้ำ abc ก้'],
 ['upper','น้ำ abc ก้',4,7,'น้ำ ABC ก้'],
 ['normalize','น้ำ e\u0301 ก้',4,6,'น้ำ é ก้']
])await test('native selected '+key,async()=>{
 await tab('writer');let e=loc('tw-editor');await e.fill(input);
 await e.evaluate((n,r)=>{n.focus();n.setSelectionRange(r[0],r[1]);n.dispatchEvent(new Event('select'));},[start,end]);
 if(!await loc('tw-us-'+key).isVisible())await loc('tw-btn-more').click();
 await loc('tw-us-'+key).click();assert.equal(await e.inputValue(),want);
});
await test('bio native text preserved',async()=>{await tab('bio');const bio=loc('bio-input');await bio.fill('สวัสดีครับ\nน้ำ👩‍💻');await delay();const out=await loc('bio-preview').innerText();assert(out.includes('สวัสดีครับ')&&out.includes('น้ำ'));await loc('bio-copy').click();assert((await page.evaluate(()=>navigator.clipboard.readText())).includes('สวัสดีครับ'));});

await test('Thai handwriting actual loaded faces and distinct raster',async()=>{
 const names={natural:'Mali',neat:'Itim',cursive:'Sriracha',marker:'Charmonman',pacifico:'Mali',satisfy:'Srisakdi',allura:'Kodchasan',greatvibes:'Pattaya',sacramento:'Niramit'};
 const sample='สวัสดีครับ น้ำ ก้ ๑๒๓';
 assert.equal(await page.evaluate(()=>performance.getEntriesByType('resource').filter(r=>r.name.endsWith('.woff2')).length),0);
 await openExport(sample,'handwriting');const raster={};
 for(const [key,family] of Object.entries(names)){
   await page.locator('[data-hw-style="'+key+'"]').click();
   const result=await page.evaluate(async ({family,sample})=>{
     const el=document.getElementById('tw-handwriting-preview'),css=getComputedStyle(el);
     const faces=await document.fonts.load(css.fontWeight+' 48px "'+family+'"',sample);
     const cn=document.createElement('canvas');cn.width=1200;cn.height=120;const ctx=cn.getContext('2d');
     ctx.font=css.fontWeight+' 48px "'+family+'"';ctx.fillText(sample,15,75);
     return {loaded:faces.some(f=>f.family.replaceAll('"','')===family&&f.status==='loaded'),selected:css.fontFamily.includes(family),raster:cn.toDataURL()};
   },{family,sample});
   assert(result.loaded&&result.selected,family);raster[key]=result.raster;
 }
 assert.equal(Object.keys(raster).length,9);assert.equal(new Set(Object.values(raster)).size,9);
 await page.screenshot({path:path.join(tmp,'th-handwriting-verified.png')});
});
await test('Thai long unspaced paragraph export preserves every grapheme',async()=>{
 const sample='น้ำก้สวัสดีครับ👩‍💻'.repeat(40);
 await page.evaluate(()=>{window.__thaiLines=[];const fn=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,...args){if(typeof t==='string'&&/[ก-๙]/.test(t)&&this.canvas.width===1080&&this.canvas.height===1350)window.__thaiLines.push(t);return fn.call(this,t,...args);};});
 await openExport(sample,'handwriting');await page.evaluate(()=>window.__thaiLines=[]);await loc('tw-btn-export-pdf').click();await loc('tw-result-modal').waitFor({state:'visible'});const lines=await page.evaluate(()=>window.__thaiLines);assert(lines.length>1);assert.equal(lines.join(''),sample);const boundaries=new Set(Array.from(new Intl.Segmenter('th-TH',{granularity:'grapheme'}).segment(sample),x=>x.index));boundaries.add(sample.length);let end=0;for(const line of lines){end+=line.length;assert(boundaries.has(end));}
});
await test('Thai runtime localization audit',async()=>{
 const audit={};
 for(const key of ['quick','writer','bio','pro']){
   await tab(key);audit[key]=await page.locator('#view-'+key+' button, #view-'+key+' select, #view-'+key+' input, #view-'+key+' textarea').evaluateAll(ns=>ns.filter(n=>n.getClientRects().length).map(n=>({id:n.id,text:(n.innerText||n.placeholder||n.title||'').trim().slice(0,200)})));
 }
 await writeFile(path.join(tmp,'runtime-labels.json'),JSON.stringify(audit,null,2));
 assert(!JSON.stringify(audit).match(/Type your text\.\.\.|Invisible Space|Excluir|Styled PDF|Create PNG|& ICONS|Choose Style|Add Icon/));
 assert(audit.bio.some(x=>x.text.includes('3418 สัญลักษณ์และไอคอน')),'bio icon picker localized');
 assert(audit.pro.some(x=>x.id==='lf194-btn-icon-picker'&&x.text.includes('3418 สัญลักษณ์และไอคอน')),'pro icon picker localized');
});
await writeFile(path.join(tmp,'suite.json'),JSON.stringify({results,pageErrors:errors,browser:browser.version()},null,2));console.log('TH_QA_RESULT',results.filter(r=>r.status==='PASS').length+'/'+results.length,'pageErrors',errors);
await browser.close();server.close();
if(results.some(x=>x.status==='FAIL')||errors.length)process.exitCode=1;
