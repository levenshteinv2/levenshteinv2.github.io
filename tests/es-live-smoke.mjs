import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const url='https://levenshteinv2.github.io/generador-de-letras';
const browser=await chromium.launch({headless:true});
try{
const context=await browser.newContext({permissions:['clipboard-read','clipboard-write'],viewport:{width:390,height:844}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const response=await page.goto(url,{waitUntil:'load',timeout:60000});
assert.equal(response.status(),200);assert.equal(page.url(),url);
assert.equal(await page.locator('html').getAttribute('lang'),'es-ES');assert.equal(await page.locator('h1').innerText(),'Generador de Letras');
await page.waitForFunction(()=>document.querySelectorAll('#quick-grid .lf-font-item').length===316);
await page.locator('#quick-input').fill('José, niño, pingüino');await page.waitForTimeout(350);
const styles=await page.locator('#quick-grid .lf-font-styled').allTextContents();assert.equal(styles.length,316);assert(styles.every(x=>x.normalize('NFKD').includes('\u0303')&&x.normalize('NFKD').includes('\u0308')&&x.normalize('NFKD').includes('\u0301')));
await page.locator('#quick-grid .lf-font-item').first().click();assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),styles[0]);
assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
await page.locator('[data-tab="writer"]').click();await page.locator('#tw-editor').fill('José niño');await page.locator('#tw-btn-more').click();assert(await page.locator('#tw-more-panel').isVisible());
console.log('ES_LIVE_RESULT '+JSON.stringify({url:page.url(),status:response.status(),styles:styles.length,errors,metrics:await page.evaluate(()=>{const n=performance.getEntriesByType('navigation')[0];return {domContentLoadedMs:Math.round(n.domContentLoadedEventEnd),loadMs:Math.round(n.loadEventEnd),htmlTransferBytes:n.transferSize}})}));
assert.equal(errors.length,0);
}finally{await browser.close();}
