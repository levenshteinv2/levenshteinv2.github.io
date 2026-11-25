// FILE IMPORT HELPERS: DOCX + PDF text layer (self-contained, no OCR)
async function twReadDocxText(file){
  if(typeof JSZip==='undefined') throw new Error('ระบบ DOCX ยังไม่พร้อมใช้งาน');
  const buf=await file.arrayBuffer();
  const zip=await JSZip.loadAsync(buf);
  const main=zip.file('word/document.xml');
  if(!main) throw new Error('DOCX inválido: word/document.xml não encontrado');
  const xml=await main.async('string');
  const doc=new DOMParser().parseFromString(xml,'application/xml');
  if(doc.getElementsByTagName('parsererror').length) throw new Error('ไม่สามารถอ่าน XML ของ DOCX ได้');
  const paragraphs=Array.from(doc.getElementsByTagName('w:p'));
  function nodeText(node){
    let out='';
    for(const ch of Array.from(node.childNodes||[])){
      const n=ch.nodeName;
      if(n==='w:t') out+=ch.textContent||'';
      else if(n==='w:tab') out+='\t';
      else if(n==='w:br' || n==='w:cr') out+='\n';
      else out+=nodeText(ch);
    }
    return out;
  }
  const lines=paragraphs.map(p=>nodeText(p).replace(/\u00a0/g,' '));
  // Keep paragraph order and intentional blank paragraphs; trim only the file edges.
  return lines.join('\n').replace(/^\s*\n/,'').replace(/\n\s*$/,'').trimEnd();
}

function twBytesToBinaryString(bytes){
  let out='';
  const step=0x8000;
  for(let i=0;i<bytes.length;i+=step) out+=String.fromCharCode.apply(null,bytes.subarray(i,Math.min(i+step,bytes.length)));
  return out;
}

async function twInflatePdf(bytes, rawMode){
  if(typeof DecompressionStream==='undefined') throw new Error('Este navegador não oferece suporte à extração de PDF');
  const fmt=rawMode?'deflate-raw':'deflate';
  const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream(fmt));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

function twPdfParseObjects(bytes){
  const src=twBytesToBinaryString(bytes);
  const objs=new Map();
  const order=[];
  const re=/(\d+)\s+(\d+)\s+obj\b/g;
  let m;
  while((m=re.exec(src))){
    const id=Number(m[1]);
    const bodyStart=re.lastIndex;
    const end=src.indexOf('endobj',bodyStart);
    if(end<0) break;
    const raw=src.slice(bodyStart,end);
    const streamToken=raw.indexOf('stream');
    let dict=raw, streamBytes=null;
    if(streamToken>=0){
      dict=raw.slice(0,streamToken);
      let rel=streamToken+6;
      if(raw.charCodeAt(rel)===13 && raw.charCodeAt(rel+1)===10) rel+=2;
      else if(raw.charCodeAt(rel)===10 || raw.charCodeAt(rel)===13) rel+=1;
      const endStream=raw.lastIndexOf('endstream');
      if(endStream>=rel){
        const absStart=bodyStart+rel;
        const absEnd=bodyStart+endStream;
        streamBytes=bytes.slice(absStart,absEnd);
        while(streamBytes.length && (streamBytes[streamBytes.length-1]===10 || streamBytes[streamBytes.length-1]===13)) streamBytes=streamBytes.slice(0,-1);
      }
    }
    objs.set(id,{id,raw,dict,streamBytes,decoded:null});
    order.push(id);
    re.lastIndex=end+6;
  }
  return {src,objs,order};
}

function twPdfAscii85Decode(bytes){
  let s=twBytesToBinaryString(bytes).replace(/\s+/g,'');
  s=s.replace(/^<~/,'').replace(/~>.*$/,'');
  const out=[]; let group=[];
  function flush(g,partial){
    const original=g.length;
    while(g.length<5) g.push('u'.charCodeAt(0));
    let n=0;
    for(const c of g) n=n*85+(c-33);
    const tmp=[(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255];
    const count=partial ? Math.max(0,original-1) : 4;
    for(let i=0;i<count;i++) out.push(tmp[i]);
  }
  for(let i=0;i<s.length;i++){
    const c=s.charCodeAt(i);
    if(s[i]==='z' && group.length===0){out.push(0,0,0,0);continue;}
    if(c<33 || c>117) continue;
    group.push(c);
    if(group.length===5){flush(group,false);group=[];}
  }
  if(group.length>1) flush(group,true);
  return new Uint8Array(out);
}

function twPdfAsciiHexDecode(bytes){
  let h=twBytesToBinaryString(bytes).replace(/\s+/g,'').replace(/>.*/, '');
  if(h.length%2) h+='0';
  const out=new Uint8Array(h.length/2);
  for(let i=0;i<out.length;i++) out[i]=parseInt(h.slice(i*2,i*2+2),16);
  return out;
}

function twPdfFilters(dict){
  const arr=dict.match(/\/Filter\s*\[([^\]]+)\]/);
  if(arr){const out=[]; const re=/\/([A-Za-z0-9]+)/g; let m; while((m=re.exec(arr[1]))) out.push(m[1]); return out;}
  const one=dict.match(/\/Filter\s*\/([A-Za-z0-9]+)/); return one?[one[1]]:[];
}

async function twPdfDecodeStreams(parsed){
  const jobs=[];
  for(const obj of parsed.objs.values()){
    if(!obj.streamBytes) continue;
    jobs.push((async()=>{
      let b=obj.streamBytes;
      try{
        for(const f of twPdfFilters(obj.dict)){
          if(f==='ASCII85Decode' || f==='A85') b=twPdfAscii85Decode(b);
          else if(f==='ASCIIHexDecode' || f==='AHx') b=twPdfAsciiHexDecode(b);
          else if(f==='FlateDecode' || f==='Fl'){
            try{b=await twInflatePdf(b,false);}catch(_e){b=await twInflatePdf(b,true);}
          } else { b=null; break; }
          if(!b) break;
        }
      }catch(_e){b=null;}
      if(b) obj.decoded=b;
    })());
  }
  await Promise.all(jobs);
}

function twPdfUtf16Be(hex){
  hex=hex.replace(/\s+/g,'');
  if(hex.length%2) hex+='0';
  const bytes=[];
  for(let i=0;i+1<hex.length;i+=2) bytes.push(parseInt(hex.slice(i,i+2),16));
  let start=(bytes[0]===0xFE&&bytes[1]===0xFF)?2:0;
  let out='';
  for(let i=start;i+1<bytes.length;i+=2) out+=String.fromCharCode((bytes[i]<<8)|bytes[i+1]);
  return out;
}

function twPdfParseCMap(text){
  const map=new Map();
  const clean=text.replace(/%[^\r\n]*/g,' ');
  let m;
  const bfchar=/beginbfchar([\s\S]*?)endbfchar/g;
  while((m=bfchar.exec(clean))){
    const pair=/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/g; let p;
    while((p=pair.exec(m[1]))) map.set(p[1].toUpperCase(),twPdfUtf16Be(p[2]));
  }
  const bfrange=/beginbfrange([\s\S]*?)endbfrange/g;
  while((m=bfrange.exec(clean))){
    const block=m[1];
    const line=/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<([0-9A-Fa-f]+)>|\[([^\]]*)\])/g; let p;
    while((p=line.exec(block))){
      const a=parseInt(p[1],16), z=parseInt(p[2],16), width=p[1].length;
      if(p[4]){
        const baseHex=p[4];
        const base=parseInt(baseHex,16);
        for(let code=a;code<=z && code-a<4096;code++){
          const dst=(base+(code-a)).toString(16).toUpperCase().padStart(baseHex.length,'0');
          map.set(code.toString(16).toUpperCase().padStart(width,'0'),twPdfUtf16Be(dst));
        }
      } else {
        const vals=[]; const vr=/<([0-9A-Fa-f]+)>/g; let v;
        while((v=vr.exec(p[5]||''))) vals.push(v[1]);
        for(let code=a,i=0;code<=z && i<vals.length;code++,i++) map.set(code.toString(16).toUpperCase().padStart(width,'0'),twPdfUtf16Be(vals[i]));
      }
    }
  }
  return map;
}

function twPdfFontRefs(raw){
  const out={};
  const blocks=[];
  let idx=0;
  while((idx=raw.indexOf('/Font',idx))>=0){
    const s=raw.indexOf('<<',idx); if(s<0) break;
    let depth=0,end=-1;
    for(let i=s;i<raw.length-1;i++){
      if(raw.slice(i,i+2)==='<<'){depth++;i++;continue;}
      if(raw.slice(i,i+2)==='>>'){depth--;i++; if(depth===0){end=i+1;break;}}
    }
    if(end>0){blocks.push(raw.slice(s+2,end-1));idx=end;}else break;
  }
  for(const b of blocks){
    const re=/\/([^\s/<>()\[\]]+)\s+(\d+)\s+\d+\s+R/g; let m;
    while((m=re.exec(b))) out[m[1]]=Number(m[2]);
  }
  return out;
}

function twPdfDirectNamedRefs(raw){
  const out={};
  const re=/\/([^\s/<>()\[\]]+)\s+(\d+)\s+\d+\s+R/g; let m;
  while((m=re.exec(raw))) out[m[1]]=Number(m[2]);
  return out;
}

function twPdfWinAnsi(bytes){
  const special={128:'€',130:'‚',131:'ƒ',132:'„',133:'…',134:'†',135:'‡',136:'ˆ',137:'‰',138:'Š',139:'‹',140:'Œ',142:'Ž',145:'‘',146:'’',147:'“',148:'”',149:'•',150:'–',151:'—',152:'˜',153:'™',154:'š',155:'›',156:'œ',158:'ž',159:'Ÿ'};
  let out='';
  for(const b of bytes) out+=special[b]||String.fromCharCode(b);
  return out;
}

function twPdfLiteralBytes(token){
  const s=token.slice(1,-1); const out=[];
  for(let i=0;i<s.length;i++){
    let c=s.charCodeAt(i)&255;
    if(c!==92){out.push(c);continue;}
    i++; if(i>=s.length) break;
    const ch=s[i];
    const simple={n:10,r:13,t:9,b:8,f:12,'(':40,')':41,'\\':92};
    if(ch in simple){out.push(simple[ch]);continue;}
    if(ch==='\r'){if(s[i+1]==='\n') i++;continue;}
    if(ch==='\n') continue;
    if(/[0-7]/.test(ch)){
      let oct=ch;
      for(let k=0;k<2 && /[0-7]/.test(s[i+1]||'');k++) oct+=s[++i];
      out.push(parseInt(oct,8)&255);continue;
    }
    out.push(ch.charCodeAt(0)&255);
  }
  return new Uint8Array(out);
}

function twPdfHexBytes(token){
  let h=token.slice(1,-1).replace(/\s+/g,''); if(h.length%2) h+='0';
  const out=new Uint8Array(h.length/2); for(let i=0;i<out.length;i++) out[i]=parseInt(h.slice(i*2,i*2+2),16);
  return out;
}

function twPdfDecodeTextBytes(bytes,cmap){
  if(bytes.length>=2 && bytes[0]===0xFE && bytes[1]===0xFF){
    let out=''; for(let i=2;i+1<bytes.length;i+=2) out+=String.fromCharCode((bytes[i]<<8)|bytes[i+1]); return out;
  }
  if(cmap && cmap.size){
    const lengths=[...new Set([...cmap.keys()].map(k=>k.length/2))].sort((a,b)=>b-a);
    let out='',i=0;
    while(i<bytes.length){
      let hit=false;
      for(const len of lengths){
        if(i+len>bytes.length) continue;
        let key=''; for(let j=0;j<len;j++) key+=bytes[i+j].toString(16).toUpperCase().padStart(2,'0');
        if(cmap.has(key)){out+=cmap.get(key);i+=len;hit=true;break;}
      }
      if(!hit){out+=twPdfWinAnsi(bytes.slice(i,i+1));i++;}
    }
    return out;
  }
  return twPdfWinAnsi(bytes);
}

function twPdfLexContent(src){
  const out=[]; let i=0;
  const ws=c=>/\s/.test(c);
  while(i<src.length){
    let c=src[i];
    if(ws(c)){i++;continue;}
    if(c==='%'){while(i<src.length && src[i]!=='\n' && src[i]!=='\r') i++;continue;}
    if(c==='('){
      const s=i++; let depth=1;
      while(i<src.length && depth){
        const ch=src[i++];
        if(ch==='\\'){ if(i<src.length){ if(src[i]==='\r' && src[i+1]==='\n') i+=2; else i++; } continue; }
        if(ch==='(') depth++; else if(ch===')') depth--;
      }
      out.push({type:'lit',raw:src.slice(s,i)}); continue;
    }
    if(c==='<'){
      if(src[i+1]==='<'){out.push({type:'op',v:'<<'});i+=2;continue;}
      const s=i++; while(i<src.length && src[i]!=='>') i++; if(i<src.length)i++;
      out.push({type:'hex',raw:src.slice(s,i)}); continue;
    }
    if(c==='>' && src[i+1]==='>'){out.push({type:'op',v:'>>'});i+=2;continue;}
    if(c==='['){out.push({type:'arrStart'});i++;continue;}
    if(c===']'){out.push({type:'arrEnd'});i++;continue;}
    if(c==='/'){
      const s=++i; while(i<src.length && !ws(src[i]) && !'[]<>()/%'.includes(src[i])) i++;
      out.push({type:'name',v:src.slice(s,i)}); continue;
    }
    const s=i; while(i<src.length && !ws(src[i]) && !'[]<>()/%'.includes(src[i])) i++;
    if(i===s){i++;continue;}
    const v=src.slice(s,i);
    if(/^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(v)) out.push({type:'num',v:Number(v)});
    else out.push({type:'op',v});
  }
  return out;
}

function twPdfMatMul(a,b){
  return [
    a[0]*b[0]+a[2]*b[1], a[1]*b[0]+a[3]*b[1],
    a[0]*b[2]+a[2]*b[3], a[1]*b[2]+a[3]*b[3],
    a[0]*b[4]+a[2]*b[5]+a[4], a[1]*b[4]+a[3]*b[5]+a[5]
  ];
}
function twPdfPoint(m,x,y){return {x:m[0]*x+m[2]*y+m[4],y:m[1]*x+m[3]*y+m[5]};}

function twPdfExtractFromContent(content,fontRefs,fontCMaps){
  const toks=twPdfLexContent(content);
  let stack=[], arrStack=[];
  let currentFont=null,fontSize=12,leading=0,charSpace=0,wordSpace=0,hScale=1;
  let x=0,y=0,lineX=0,lineY=0;
  let ctm=[1,0,0,1,0,0], gstack=[];
  let seq=0; const frags=[];

  function decodeTok(t){
    const cmap=fontCMaps.get(fontRefs[currentFont])||null;
    if(!t) return '';
    if(t.type==='lit') return twPdfDecodeTextBytes(twPdfLiteralBytes(t.raw),cmap);
    if(t.type==='hex') return twPdfDecodeTextBytes(twPdfHexBytes(t.raw),cmap);
    return '';
  }
  function approxAdvance(text){
    if(!text) return 0;
    let n=[...text].length;
    let spaces=(text.match(/ /g)||[]).length;
    return Math.max(0,fontSize*(0.48*n)+charSpace*Math.max(0,n-1)+wordSpace*spaces)*hScale;
  }
  function showText(text){
    text=(text||'').replace(/\u0000/g,''); if(!text) return;
    const p=twPdfPoint(ctm,x,y);
    const adv=approxAdvance(text);
    const p2=twPdfPoint(ctm,x+adv,y);
    frags.push({text,x:p.x,y:p.y,endX:p2.x,fontSize:Math.max(1,Math.abs(fontSize)),seq:seq++});
    x+=adv;
  }
  function showArray(arr){
    for(const t of arr||[]){
      if(t.type==='lit'||t.type==='hex') showText(decodeTok(t));
      else if(t.type==='num') x += (-t.v/1000)*fontSize*hScale;
    }
  }
  function nextLine(){ const dy=leading||fontSize*1.2; lineY-=dy; x=lineX; y=lineY; }
  function operands(n){return stack.splice(Math.max(0,stack.length-n),n);}

  for(let ti=0;ti<toks.length;ti++){
    const t=toks[ti];
    if(t.type==='arrStart'){arrStack.push([]);continue;}
    if(t.type==='arrEnd'){
      const arr=arrStack.pop()||[];
      if(arrStack.length) arrStack[arrStack.length-1].push({type:'array',v:arr}); else stack.push({type:'array',v:arr});
      continue;
    }
    if(arrStack.length && t.type!=='op'){arrStack[arrStack.length-1].push(t);continue;}
    if(t.type!=='op'){stack.push(t);continue;}
    const op=t.v;
    // Bare values accidentally lexed as operators should be ignored unless recognized below.
    if(op==='q'){gstack.push(ctm.slice());stack=[];continue;}
    if(op==='Q'){ctm=gstack.pop()||[1,0,0,1,0,0];stack=[];continue;}
    if(op==='cm'){
      const a=operands(6).map(v=>v.v); if(a.length===6 && a.every(Number.isFinite)) ctm=twPdfMatMul(ctm,a);
      stack=[];continue;
    }
    if(op==='BT'){x=y=lineX=lineY=0;stack=[];continue;}
    if(op==='ET'){stack=[];continue;}
    if(op==='Tf'){
      const a=operands(2); if(a[0]&&a[0].type==='name') currentFont=a[0].v; if(a[1]&&a[1].type==='num') fontSize=Math.abs(a[1].v)||fontSize;
      stack=[];continue;
    }
    if(op==='Tm'){
      const a=operands(6).map(v=>v.v); if(a.length===6){x=lineX=a[4]||0;y=lineY=a[5]||0;}
      stack=[];continue;
    }
    if(op==='Td'||op==='TD'){
      const a=operands(2).map(v=>v.v); if(a.length===2){lineX+=a[0]||0;lineY+=a[1]||0;x=lineX;y=lineY;if(op==='TD')leading=-(a[1]||0);}
      stack=[];continue;
    }
    if(op==='T*'){nextLine();stack=[];continue;}
    if(op==='TL'){const a=operands(1)[0]; if(a&&a.type==='num')leading=a.v;stack=[];continue;}
    if(op==='Tc'){const a=operands(1)[0]; if(a&&a.type==='num')charSpace=a.v;stack=[];continue;}
    if(op==='Tw'){const a=operands(1)[0]; if(a&&a.type==='num')wordSpace=a.v;stack=[];continue;}
    if(op==='Tz'){const a=operands(1)[0]; if(a&&a.type==='num')hScale=a.v/100;stack=[];continue;}
    if(op==='Tj'){
      const a=operands(1)[0]; if(a&&(a.type==='lit'||a.type==='hex'))showText(decodeTok(a)); stack=[];continue;
    }
    if(op==='TJ'){
      const a=operands(1)[0]; if(a&&a.type==='array')showArray(a.v); stack=[];continue;
    }
    if(op==="'"){
      nextLine(); const a=operands(1)[0]; if(a&&(a.type==='lit'||a.type==='hex'))showText(decodeTok(a)); stack=[];continue;
    }
    if(op==='"'){
      const a=operands(3); if(a[0]&&a[0].type==='num')wordSpace=a[0].v;if(a[1]&&a[1].type==='num')charSpace=a[1].v;nextLine();if(a[2]&&(a[2].type==='lit'||a[2].type==='hex'))showText(decodeTok(a[2])); stack=[];continue;
    }
    // Keep operands for unknown text-state operators only briefly; most operators terminate an operand sequence.
    stack=[];
  }

  if(!frags.length) return '';

  // Cluster fragments into visual lines using Y coordinates. This avoids treating every ET/Td as a hard line break.
  const sorted=frags.slice().sort((a,b)=>Math.abs(b.y-a.y)>1 ? b.y-a.y : (a.x-b.x || a.seq-b.seq));
  const lines=[];
  for(const f of sorted){
    let best=null,bestDy=Infinity;
    for(const ln of lines){
      const tol=Math.max(2.2,Math.min(7,Math.max(f.fontSize,ln.fontSize)*0.34));
      const dy=Math.abs(ln.y-f.y);
      if(dy<=tol && dy<bestDy){best=ln;bestDy=dy;}
    }
    if(!best){best={y:f.y,fontSize:f.fontSize,frags:[]};lines.push(best);}
    best.frags.push(f); best.fontSize=Math.max(best.fontSize,f.fontSize);
  }
  lines.sort((a,b)=>b.y-a.y);

  function lineText(ln){
    const fs=ln.frags.slice().sort((a,b)=>a.x-b.x || a.seq-b.seq);
    let s='',prev=null;
    for(const f of fs){
      let txt=(f.text||'').replace(/[\r\n\t]+/g,' ').replace(/ {2,}/g,' ');
      if(!txt) continue;
      if(prev && s && !/\s$/.test(s) && !/^\s/.test(txt)){
        const gap=f.x-prev.endX;
        const unit=Math.max(2,Math.min(prev.fontSize,f.fontSize));
        // Coordinates are authoritative: visible gap => word boundary; overlap/tiny gap => same word.
        if(gap>unit*0.11) s+=' ';
      }
      s+=txt;
      prev=f;
    }
    return s.replace(/\s{2,}/g,' ').trim();
  }

  const rows=lines.map(ln=>({text:lineText(ln),y:ln.y,fontSize:ln.fontSize})).filter(r=>r.text);
  if(!rows.length) return '';
  const gaps=[];
  for(let i=1;i<rows.length;i++){const g=Math.abs(rows[i-1].y-rows[i].y);if(g>1&&g<100)gaps.push(g);}
  gaps.sort((a,b)=>a-b);
  const median=gaps.length ? gaps[Math.floor(gaps.length/2)] : 0;
  const common=new Set(['the','and','for','with','from','this','that','are','was','were','have','has','had','to','of','in','on','at','by','as','or','an','a','is','it','its','be','between','into','than','then','when','where','which']);
  function mergeBoundary(a,b){
    if(!a) return b;if(!b)return a;
    if(/[-‐‑‒–—]$/.test(a) && /^[\p{L}\p{N}]/u.test(b)) return a.replace(/[-‐‑‒–—]$/,'')+b;
    const m=b.match(/^([\p{Ll}]{2,4})(?=\s|$)/u);
    const last=(a.match(/([\p{L}]+)$/u)||[])[1]||'';
    if(m && last.length>=3 && !common.has(m[1].toLowerCase())) return a+b;
    return a+' '+b;
  }

  let out=rows[0].text;
  for(let i=1;i<rows.length;i++){
    const prev=rows[i-1],cur=rows[i];
    const gap=Math.abs(prev.y-cur.y);
    const bigGap=median>0 && gap>median*1.65;
    const fontJump=Math.abs(prev.fontSize-cur.fontSize)>Math.max(2.5,Math.min(prev.fontSize,cur.fontSize)*0.28);
    const prevHeading=prev.text.length<90 && fontJump;
    if(bigGap || prevHeading){out+='\n\n'+cur.text;}
    else out=mergeBoundary(out,cur.text);
  }
  return out.replace(/[ \t]+\n/g,'\n').replace(/\n{3,}/g,'\n\n').replace(/ {2,}/g,' ').trim();
}
async function twReadPdfTextLayer(file){
  const bytes=new Uint8Array(await file.arrayBuffer());
  if(bytes.length<5 || String.fromCharCode(...bytes.slice(0,5))!=='%PDF-') throw new Error('PDF inválido');
  const parsed=twPdfParseObjects(bytes);
  await twPdfDecodeStreams(parsed);

  const fontCMaps=new Map();
  for(const obj of parsed.objs.values()){
    const m=obj.dict.match(/\/ToUnicode\s+(\d+)\s+\d+\s+R/);
    if(m){
      const cmapObj=parsed.objs.get(Number(m[1]));
      if(cmapObj && cmapObj.decoded){
        try{ fontCMaps.set(obj.id,twPdfParseCMap(twBytesToBinaryString(cmapObj.decoded))); }catch(_e){}
      }
    }
  }
  const globalFonts={};
  for(const obj of parsed.objs.values()){
    Object.assign(globalFonts,twPdfFontRefs(obj.raw));
    if(/\/Type\s*\/Font\b/.test(obj.raw)){
      const n=obj.raw.match(/\/Name\s*\/([^\s/<>()\[\]]+)/);
      if(n) globalFonts[n[1]]=obj.id;
    }
  }

  const pages=[];
  for(const id of parsed.order){
    const obj=parsed.objs.get(id); if(!obj || !/\/Type\s*\/Page\b/.test(obj.raw)) continue;
    let refs=[];
    let m=obj.raw.match(/\/Contents\s+(\d+)\s+\d+\s+R/); if(m) refs=[Number(m[1])];
    const a=obj.raw.match(/\/Contents\s*\[([^\]]+)\]/); if(a){refs=[]; const rr=/(\d+)\s+\d+\s+R/g; let q; while((q=rr.exec(a[1]))) refs.push(Number(q[1]));}
    let resRaw=obj.raw;
    const fonts=Object.assign({},globalFonts);
    const r=obj.raw.match(/\/Resources\s+(\d+)\s+\d+\s+R/);
    if(r && parsed.objs.get(Number(r[1]))) resRaw+='\n'+parsed.objs.get(Number(r[1])).raw;
    Object.assign(fonts,twPdfFontRefs(resRaw));
    const fr=resRaw.match(/\/Font\s+(\d+)\s+\d+\s+R/);
    if(fr && parsed.objs.get(Number(fr[1]))) Object.assign(fonts,twPdfDirectNamedRefs(parsed.objs.get(Number(fr[1])).raw));
    pages.push({refs,fonts});
  }

  const chunks=[]; const used=new Set();
  const process=(ref,fonts)=>{
    const obj=parsed.objs.get(ref); if(!obj || !obj.decoded) return;
    const txt=twBytesToBinaryString(obj.decoded); if(!/\bBT\b/.test(txt)) return;
    used.add(ref); const t=twPdfExtractFromContent(txt,fonts,fontCMaps); if(t) chunks.push(t);
  };
  for(const p of pages){ const before=chunks.length; for(const ref of p.refs) process(ref,p.fonts); if(chunks.length>before) chunks.push('\n'); }
  if(!chunks.length){
    for(const obj of parsed.objs.values()) if(obj.decoded && !used.has(obj.id)) process(obj.id,globalFonts);
  }
  const text=chunks.join('\n').replace(/\n{3,}/g,'\n\n').trim();
  if(!text || text.replace(/\s/g,'').length<2) throw new Error('PDF นี้ไม่มีชั้นข้อความที่อ่านได้');
  return text;
}
