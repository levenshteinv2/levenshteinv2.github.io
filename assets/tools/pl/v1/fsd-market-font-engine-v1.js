
(function(){
'use strict';
if(window.FSDMarketFonts && window.FSDMarketFonts.version)return;

const VERSION='1.0.0-global-font-engine';
const MARKET_ALIASES={
  'vi':'vi','vi-vn':'vi',
  'en':'en','en-us':'en','en-gb':'en','en-in':'en',
  'pt':'pt-BR','pt-br':'pt-BR',
  'es':'es-bonitas','es-es':'es-bonitas','es-mx':'es-bonitas','es-generator':'es-generator','es-bonitas':'es-bonitas',
  'de':'de','de-de':'de',
  'ru':'ru','ru-ru':'ru',
  'tr':'tr','tr-tr':'tr',
  'ja':'ja','ja-jp':'ja',
  'th':'th','th-th':'th',
  'id':'id','id-id':'id',
  'fr':'fr','fr-fr':'fr'
};
function detectMarket(){
  let q='';try{q=new URLSearchParams(location.search).get('market')||'';}catch(_){}
  const raw=String(q||window.FSD_MARKET||document.documentElement.lang||'en').trim();
  return MARKET_ALIASES[raw]||MARKET_ALIASES[raw.toLowerCase()]||MARKET_ALIASES[raw.toLowerCase().split('-')[0]]||'en';
}
const MARKET='pl';

const CORE_PRIORITY={
  'vi':['Script','Bold Script','Bold','Sans Bold','Italic','Bold Italic','Sans','Sans Italic','Sans Bold Italic','Monospace','Double Struck','Small Caps','Old English','Fraktur','Bold Fraktur','Medieval','Typewriter Bold','Superscript','Subscript'],
  'en':['Bold','Script','Bold Script','Sans Bold','Italic','Bold Italic','Sans','Sans Italic','Fraktur','Bold Fraktur','Double Struck','Circled','Fullwidth','Small Caps','Monospace','Squared','Cute','Old English','Typewriter Bold','Negative Circled','Superscript','Subscript','Upside Down'],
  'pt-BR':['Script','Bold Script','Bold','Italic','Bold Italic','Small Caps','Sans Bold','Sans','Sans Italic','Double Struck','Fraktur','Bold Fraktur','Old English','Monospace','Medieval','Typewriter Bold','Superscript','Subscript'],
  'es-bonitas':['Script','Bold Script','Italic','Bold Italic','Bold','Small Caps','Sans Bold','Sans','Sans Italic','Double Struck','Fraktur','Bold Fraktur','Old English','Monospace','Medieval','Typewriter Bold','Superscript','Subscript'],
  'es-generator':['Bold','Script','Bold Script','Sans Bold','Italic','Bold Italic','Circled','Fullwidth','Small Caps','Fraktur','Double Struck','Monospace','Cute','Squared'],
  'de':['Fraktur','Bold Fraktur','Old English','Script','Bold Script','Bold','Sans Bold','Italic','Bold Italic','Small Caps','Double Struck','Monospace','Sans','Sans Italic','Medieval','Typewriter Bold'],
  'ru':[],
  'tr':['Bold','Script','Bold Script','Sans Bold','Italic','Bold Italic','Sans','Sans Italic','Small Caps','Fraktur','Bold Fraktur','Double Struck','Monospace','Old English','Medieval','Typewriter Bold'],
  'ja':['Fullwidth','Circled','Squared','White Squared','Double Circled','Negative Circled','Monospace','Bold','Sans Bold','Small Caps','Script','Cute'],
  'th':[],
  'id':['Script','Bold Script','Fullwidth','Small Caps','Cute','Double Struck','Circled','Sans','Sans Bold','Italic','Bold','Fraktur','Monospace','Squared','Negative Circled'],
  'fr':['Script','Bold Script','Italic','Bold Italic','Bold','Sans','Sans Bold','Sans Italic','Double Struck','Small Caps','Fraktur','Bold Fraktur','Old English','Monospace','Medieval','Typewriter Bold','Superscript','Subscript']
};

CORE_PRIORITY["pl"]=["Bold","Script","Bold Script","Sans Bold","Italic","Bold Italic","local-underline","local-double-underline","local-strike","local-overline","local-dot-below","local-wide","local-heart-frame","local-star-frame","local-sparkle-frame","local-box-frame","local-angle-frame","local-crown-frame","local-flower-frame","Small Caps","Fraktur","Bold Fraktur","Monospace"];

const LOCAL_LABELS={
  'vi':{
    underline:'Gạch chân',doubleUnderline:'Gạch chân đôi',strike:'Gạch ngang',overline:'Gạch trên',dotBelow:'Chấm dưới',wide:'Giãn chữ',dotSep:'Chấm giữa',starSep:'Ngăn sao',heartSep:'Ngăn tim',sparkleSep:'Ngăn lấp lánh',heartFrame:'Khung trái tim',starFrame:'Khung ngôi sao',sparkleFrame:'Khung lấp lánh',softFrame:'Khung mềm',boxFrame:'Khung vuông',angleFrame:'Khung góc',doubleAngle:'Khung đôi',khmerFrame:'Khung nghệ thuật',lotusFrame:'Khung hoa văn',wingFrame:'Khung cánh',crownFrame:'Khung vương miện',flowerFrame:'Khung hoa',waveFrame:'Khung sóng',reverse:'Đảo ngược',cursed:'Nhiễu nhẹ'
  },
  'ru':{
    underline:'Подчёркнутый',doubleUnderline:'Двойное подчёркивание',strike:'Зачёркнутый',overline:'Надчёркнутый',dotBelow:'Точки снизу',wide:'Разрядка',dotSep:'Через точку',starSep:'Через звёзды',heartSep:'Через сердца',sparkleSep:'Через искры',heartFrame:'Рамка с сердцами',starFrame:'Звёздная рамка',sparkleFrame:'Рамка с искрами',softFrame:'Мягкая рамка',boxFrame:'【Квадратная рамка】',angleFrame:'『Угловая рамка』',doubleAngle:'《Двойная рамка》',khmerFrame:'꧁ Декоративная рамка ꧂',lotusFrame:'༺ Орнамент ༻',wingFrame:'𓆩 Крылья 𓆪',crownFrame:'♛ Корона ♛',flowerFrame:'✿ Цветы ✿',waveFrame:'〜 Волна 〜',reverse:'Обратный текст',cursed:'Лёгкий glitch',ruQuote:'«Русская рамка»',ruDot:'Разрядка •',ruStar:'Русские звёзды'
  },
  'ja':{
    underline:'下線',doubleUnderline:'二重下線',strike:'取り消し線',overline:'上線',dotBelow:'点付き',wide:'文字間隔',dotSep:'中黒区切り',starSep:'星区切り',heartSep:'ハート区切り',sparkleSep:'キラキラ区切り',heartFrame:'ハート枠',starFrame:'星枠',sparkleFrame:'キラキラ枠',softFrame:'やわらか枠',boxFrame:'【すみ付き括弧】',angleFrame:'『二重かぎ括弧』',doubleAngle:'《二重山括弧》',khmerFrame:'꧁ デコ枠 ꧂',lotusFrame:'༺ デコレーション ༻',wingFrame:'𓆩 ウイング 𓆪',crownFrame:'♛ クラウン ♛',flowerFrame:'✿ フラワー ✿',waveFrame:'〜 波線 〜',reverse:'逆順',cursed:'グリッチ',hiraToKata:'ひらがな → カタカナ',kataToHira:'カタカナ → ひらがな',halfKata:'半角カタカナ',jpQuote:'「かぎ括弧」',jpTortoise:'〔括弧〕',jpWhite:'〖白角括弧〗',circleFrame:'丸フレーム',diamondFrame:'ひし形フレーム',musicFrame:'音符フレーム',arrowFrame:'矢印フレーム'
  },
  'th':{
    underline:'ขีดเส้นใต้',doubleUnderline:'ขีดเส้นใต้คู่',strike:'ขีดฆ่า',overline:'ขีดบน',dotBelow:'จุดด้านล่าง',wide:'เว้นระยะ',dotSep:'คั่นด้วยจุด',starSep:'คั่นด้วยดาว',heartSep:'คั่นด้วยหัวใจ',sparkleSep:'คั่นด้วยประกาย',heartFrame:'กรอบหัวใจ',starFrame:'กรอบดาว',sparkleFrame:'กรอบประกาย',softFrame:'กรอบนุ่ม',boxFrame:'【กรอบสี่เหลี่ยม】',angleFrame:'『กรอบญี่ปุ่น』',doubleAngle:'《กรอบคู่》',khmerFrame:'꧁ กรอบศิลป์ ꧂',lotusFrame:'༺ กรอบลาย ༻',wingFrame:'𓆩 กรอบปีก 𓆪',crownFrame:'♛ กรอบมงกุฎ ♛',flowerFrame:'✿ กรอบดอกไม้ ✿',waveFrame:'〜 กรอบคลื่น 〜',reverse:'กลับข้อความ',cursed:'กลิตช์เบา',thaiDigits:'เลขไทย',thaiOrb:'๏ กรอบไทย ๏',thaiEnd:'๛ กรอบไทย ๛',thaiDecor:'๚ กรอบไทย ๚',circleFrame:'กรอบวงกลม',diamondFrame:'กรอบเพชร',musicFrame:'กรอบดนตรี',arrowFrame:'กรอบลูกศร'
  },
  'tr':{cursed:'Zalgo Hafif',heartFrame:'Kalp Çerçeve',starFrame:'Yıldız Çerçeve',sparkleFrame:'Parıltı Çerçeve',softFrame:'Yumuşak Çerçeve',strike:'Üstü Çizili',doubleUnderline:'Çift Altı Çizili',boxFrame:'Kutu Çerçeve',crownFrame:'Taç Çerçeve',flowerFrame:'Çiçek Çerçeve'},
  'id':{heartFrame:'Bingkai Hati',starFrame:'Bingkai Bintang',sparkleFrame:'Bingkai Kilau',softFrame:'Bingkai Soft',strike:'Coret',doubleUnderline:'Garis Bawah Ganda',boxFrame:'Bingkai Kotak',crownFrame:'Bingkai Mahkota',flowerFrame:'Bingkai Bunga',cursed:'Glitch Ringan'},
  'fr':{heartFrame:'Cadre Cœur',starFrame:'Cadre Étoile',sparkleFrame:'Cadre Étincelle',softFrame:'Cadre Doux',strike:'Barré',doubleUnderline:'Double souligné',boxFrame:'Cadre',crownFrame:'Cadre Couronne',flowerFrame:'Cadre Fleur',cursed:'Glitch léger'},
  'de':{heartFrame:'Herzrahmen',starFrame:'Sternrahmen',sparkleFrame:'Glitzerrahmen',softFrame:'Weicher Rahmen',strike:'Durchgestrichen',doubleUnderline:'Doppelt unterstrichen',boxFrame:'Kastenrahmen',crownFrame:'Kronenrahmen',flowerFrame:'Blumenrahmen',cursed:'Leichter Glitch'},
  'pt-BR':{heartFrame:'Moldura de Coração',starFrame:'Moldura de Estrela',sparkleFrame:'Moldura Brilhante',softFrame:'Moldura Suave',strike:'Tachado',doubleUnderline:'Sublinhado Duplo',boxFrame:'Moldura',crownFrame:'Moldura de Coroa',flowerFrame:'Moldura Floral',cursed:'Glitch Leve'},
  'es-bonitas':{heartFrame:'Marco de Corazón',starFrame:'Marco de Estrellas',sparkleFrame:'Marco Brillante',softFrame:'Marco Suave',strike:'Tachado',doubleUnderline:'Doble Subrayado',boxFrame:'Marco',crownFrame:'Marco Corona',flowerFrame:'Marco Floral',cursed:'Glitch Suave'},
  'es-generator':{heartFrame:'Marco de Corazón',starFrame:'Marco de Estrellas',sparkleFrame:'Marco Brillante',softFrame:'Marco Suave',strike:'Tachado',doubleUnderline:'Doble Subrayado',boxFrame:'Marco',crownFrame:'Marco Corona',flowerFrame:'Marco Floral',cursed:'Glitch Suave'},
  'en':{heartFrame:'Heart Decorated',starFrame:'Star Decorated',sparkleFrame:'Sparkle Decorated',softFrame:'Soft Frame',strike:'Strikethrough',doubleUnderline:'Double Underline',boxFrame:'Box Frame',crownFrame:'Crown Frame',flowerFrame:'Flower Frame',cursed:'Cursed Light'}
};

LOCAL_LABELS["pl"]={"underline":"Podkreślenie","doubleUnderline":"Podwójne podkreślenie","strike":"Przekreślenie","overline":"Linia nad tekstem","dotBelow":"Kropki pod spodem","wide":"Rozstrzelone","dotSep":"Kropki między literami","starSep":"Gwiazdy między literami","heartSep":"Serca między literami","sparkleSep":"Iskry między literami","heartFrame":"Ramka z serc","starFrame":"Ramka z gwiazd","sparkleFrame":"Ramka z iskier","softFrame":"Miękka ramka","boxFrame":"Ramka kwadratowa","angleFrame":"Ramka narożna","doubleAngle":"Podwójna ramka","khmerFrame":"Ozdobna ramka","lotusFrame":"Ornament","wingFrame":"Ramka skrzydła","crownFrame":"Ramka korona","flowerFrame":"Ramka kwiaty","waveFrame":"Ramka fala","reverse":"Odwrócony tekst","cursed":"Lekki glitch"};

const COMMON_LATIN=['local-heart-frame','local-star-frame','local-sparkle-frame','local-soft-frame','local-strike','local-double-underline','local-box-frame','local-crown-frame','local-flower-frame','local-cursed','local-dot-sep','local-star-sep','local-heart-sep','local-sparkle-sep','local-wave-frame','local-angle-frame'];
const NATIVE_RU=['local-underline','local-double-underline','local-strike','local-overline','local-dot-below','local-wide','local-dot-sep','local-star-sep','local-heart-sep','local-sparkle-sep','local-heart-frame','local-star-frame','local-sparkle-frame','local-soft-frame','local-box-frame','local-angle-frame','local-double-angle','local-khmer-frame','local-lotus-frame','local-wing-frame','local-crown-frame','local-flower-frame','local-wave-frame','local-ru-quote','local-reverse','local-cursed'];
const NATIVE_JA=['local-jp-hira-kata','local-jp-kata-hira','local-jp-half-kata','local-wide','local-dot-sep','local-star-sep','local-heart-sep','local-sparkle-sep','local-box-frame','local-angle-frame','local-jp-quote','local-double-angle','local-jp-tortoise','local-jp-white','local-heart-frame','local-star-frame','local-sparkle-frame','local-soft-frame','local-flower-frame','local-wave-frame','local-crown-frame','local-wing-frame','local-circle-frame','local-diamond-frame','local-music-frame','local-arrow-frame','local-reverse'];
const NATIVE_TH=['local-thai-digits','local-thai-orb','local-thai-end','local-thai-decor','local-heart-frame','local-star-frame','local-sparkle-frame','local-flower-frame','local-soft-frame','local-khmer-frame','local-lotus-frame','local-wing-frame','local-crown-frame','local-box-frame','local-angle-frame','local-double-angle','local-wide','local-dot-sep','local-star-sep','local-heart-sep','local-sparkle-sep','local-circle-frame','local-diamond-frame','local-music-frame','local-arrow-frame'];
const EXTENDED_LATIN=["local-underline","local-double-underline","local-strike","local-overline","local-dot-below","local-wide","local-heart-frame","local-star-frame","local-sparkle-frame","local-soft-frame","local-box-frame","local-crown-frame","local-flower-frame","local-dot-sep","local-star-sep","local-heart-sep","local-sparkle-sep","local-wave-frame","local-angle-frame","local-reverse","local-cursed"];
const NATIVE_IN=["local-underline","local-double-underline","local-strike","local-overline","local-dot-below","local-wide","local-heart-frame","local-star-frame","local-sparkle-frame","local-soft-frame","local-box-frame","local-crown-frame","local-flower-frame","local-dot-sep","local-star-sep","local-heart-sep","local-sparkle-sep","local-wave-frame","local-angle-frame","local-reverse","local-cursed","local-in-danda","local-in-om","local-in-digits"];
const NATIVE_ZH=["local-zh-corner","local-zh-double","local-zh-book","local-zh-white","local-zh-tortoise","local-heart-frame","local-star-frame","local-sparkle-frame","local-flower-frame","local-soft-frame","local-box-frame","local-angle-frame","local-double-angle","local-circle-frame","local-diamond-frame","local-music-frame","local-arrow-frame","local-wide","local-dot-sep","local-star-sep","local-heart-sep","local-sparkle-sep","local-wave-frame","local-crown-frame","local-wing-frame"];

const LOCAL_PRIORITY={
  'vi':['Script','Bold Script','Bold','Sans Bold','local-heart-frame','local-star-frame','Italic','Bold Italic','local-sparkle-frame','Small Caps','Double Struck','local-soft-frame','Fraktur','Bold Fraktur'],
  'en':['Bold','Script','Bold Script','Sans Bold','Italic','Bold Italic','Fraktur','Bold Fraktur','local-heart-frame','Circled','Fullwidth','Small Caps','local-star-frame','Monospace','Double Struck'],
  'pt-BR':['Script','Bold Script','local-heart-frame','Bold','Italic','Small Caps','local-star-frame','Fraktur','Bold Fraktur','local-sparkle-frame','Double Struck','local-soft-frame','Sans Bold','Monospace'],
  'es-bonitas':['Script','Bold Script','local-heart-frame','Italic','Bold Italic','local-flower-frame','Small Caps','local-sparkle-frame','Double Struck','Fraktur','local-soft-frame','Bold','Sans Bold','Monospace'],
  'es-generator':['Bold','Script','Bold Script','Sans Bold','local-star-frame','Italic','Bold Italic','Circled','Fullwidth','Small Caps','local-box-frame','Fraktur'],
  'de':['Fraktur','Bold Fraktur','Old English','Script','Bold Script','Bold','local-star-frame','Small Caps','local-box-frame','Double Struck','Sans Bold','Monospace'],
  'ru':NATIVE_RU,
  'tr':['Bold','Script','Bold Script','Sans Bold','Italic','local-star-frame','Small Caps','Fraktur','local-cursed','local-heart-frame','Double Struck','local-soft-frame','Monospace'],
  'ja':NATIVE_JA,
  'th':NATIVE_TH,
  'id':['Script','Bold Script','Fullwidth','Small Caps','Cute','local-soft-frame','local-heart-frame','Double Struck','Circled','local-sparkle-frame','Sans','Fraktur','local-star-frame','Monospace'],
  'fr':['Script','Bold Script','Italic','local-heart-frame','Bold Italic','Bold','Sans','local-sparkle-frame','Double Struck','Small Caps','Fraktur','local-soft-frame','Bold Fraktur','Monospace']
};

const records=[];
const arraysByScope={};
const COMBINING=/\p{M}/u;
const LETTER_OR_NUMBER=/[\p{L}\p{N}]/u;

function label(key,fallback){return (LOCAL_LABELS[MARKET]&&LOCAL_LABELS[MARKET][key])||fallback;}
function graphemes(text){
  try{if(window.Intl&&Intl.Segmenter){const seg=new Intl.Segmenter(undefined,{granularity:'grapheme'});return Array.from(seg.segment(String(text)),x=>x.segment);}}catch(_){}
  return Array.from(String(text));
}
function splitWordsKeepSpaces(text){return String(text).split(/(\s+)/);}
function joinWithinWords(text,sep){return splitWordsKeepSpaces(text).map(part=>/\s+/.test(part)?part:graphemes(part).join(sep)).join('');}
function addCombining(text,mark){return graphemes(text).map(g=>/\s/.test(g)?g:g+mark).join('');}
function frame(text,pre,post){return pre+String(text)+post;}
function idObj(id,name,fn){return {fsdMarketId:id,name,fn,type:'local',_fsdLocal:true};}

function insertMarks(styled,marks){
  if(!marks)return styled;
  const a=Array.from(styled),tail=[];
  while(a.length&&COMBINING.test(a[a.length-1]))tail.unshift(a.pop());
  return a.join('')+marks+tail.join('');
}
const SPECIAL_LATIN={
  'Đ':['D','\u0335'],'đ':['d','\u0335'],'Ł':['L','\u0335'],'ł':['l','\u0335'],'Ø':['O','\u0338'],'ø':['o','\u0338']
};
function transformLatinExtendedChar(ch,baseFn){
  if(SPECIAL_LATIN[ch]){
    const [base,mark]=SPECIAL_LATIN[ch];
    try{return insertMarks(baseFn(base),mark);}catch(_){return ch;}
  }
  const nfd=String(ch).normalize('NFD'),a=Array.from(nfd),base=a.shift()||ch,marks=a.join('');
  if(/^[A-Za-z0-9]$/.test(base)){
    try{return insertMarks(baseFn(base),marks);}catch(_){return ch;}
  }
  try{return baseFn(ch);}catch(_){return ch;}
}
function accentAware(fn){
  if(typeof fn!=='function'||fn._fsdAccentAware)return fn;
  const wrapped=function(text){return Array.from(String(text==null?'':text)).map(ch=>transformLatinExtendedChar(ch,fn)).join('');};
  try{Object.defineProperty(wrapped,'_fsdAccentAware',{value:true});Object.defineProperty(wrapped,'_fsdOriginal',{value:fn});}catch(_){}
  return wrapped;
}

function hiraToKata(text){return Array.from(String(text)).map(ch=>{const cp=ch.codePointAt(0);return cp>=0x3041&&cp<=0x3096?String.fromCodePoint(cp+0x60):ch;}).join('');}
function kataToHira(text){return Array.from(String(text)).map(ch=>{const cp=ch.codePointAt(0);return cp>=0x30A1&&cp<=0x30F6?String.fromCodePoint(cp-0x60):ch;}).join('');}
const HALF_KATA=(function(){
  const m=new Map();
  try{
    const halves=[];for(let cp=0xFF61;cp<=0xFF9F;cp++)halves.push(String.fromCodePoint(cp));
    for(const h of halves){const f=h.normalize('NFKC');if(f&&Array.from(f).length===1)m.set(f,h);}
    const marks=['ﾞ','ﾟ'];
    for(const h of halves)for(const mark of marks){const f=(h+mark).normalize('NFKC');if(f&&Array.from(f).length===1)m.set(f,h+mark);}
  }catch(_){}
  return m;
})();
function toHalfKata(text){return Array.from(String(text)).map(ch=>HALF_KATA.get(ch)||ch).join('');}
function thaiDigits(text){const d={'0':'๐','1':'๑','2':'๒','3':'๓','4':'๔','5':'๕','6':'๖','7':'๗','8':'๘','9':'๙'};return Array.from(String(text)).map(c=>d[c]||c).join('');}
function cursedLight(text){const marks=['\u0301','\u0307','\u0336','\u0323'];let i=0;return graphemes(text).map(g=>{if(/\s/.test(g))return g;const m=marks[i++%marks.length];return g+m;}).join('');}

function allAdditionFactories(){return {
  'local-underline':()=>idObj('local-underline',label('underline','Underline'),t=>addCombining(t,'\u0332')),
  'local-double-underline':()=>idObj('local-double-underline',label('doubleUnderline','Double Underline'),t=>addCombining(t,'\u0333')),
  'local-strike':()=>idObj('local-strike',label('strike','Strikethrough'),t=>addCombining(t,'\u0336')),
  'local-overline':()=>idObj('local-overline',label('overline','Overline'),t=>addCombining(t,'\u0305')),
  'local-dot-below':()=>idObj('local-dot-below',label('dotBelow','Dotted'),t=>addCombining(t,'\u0323')),
  'local-wide':()=>idObj('local-wide',label('wide','Wide Spaced'),t=>joinWithinWords(t,' ')),
  'local-dot-sep':()=>idObj('local-dot-sep',label('dotSep','Middle Dot'),t=>joinWithinWords(t,'·')),
  'local-star-sep':()=>idObj('local-star-sep',label('starSep','Star Separated'),t=>joinWithinWords(t,'✦')),
  'local-heart-sep':()=>idObj('local-heart-sep',label('heartSep','Heart Separated'),t=>joinWithinWords(t,'♡')),
  'local-sparkle-sep':()=>idObj('local-sparkle-sep',label('sparkleSep','Sparkle Separated'),t=>joinWithinWords(t,'⋆')),
  'local-heart-frame':()=>idObj('local-heart-frame',label('heartFrame','Heart Decorated'),t=>frame(t,'♡ ',' ♡')),
  'local-star-frame':()=>idObj('local-star-frame',label('starFrame','Star Decorated'),t=>frame(t,'★ ',' ★')),
  'local-sparkle-frame':()=>idObj('local-sparkle-frame',label('sparkleFrame','Sparkle Decorated'),t=>frame(t,'✦ ',' ✦')),
  'local-soft-frame':()=>idObj('local-soft-frame',label('softFrame','Soft Frame'),t=>frame(t,'꒰ ',' ꒱')),
  'local-box-frame':()=>idObj('local-box-frame',label('boxFrame','Box Frame'),t=>frame(t,'【','】')),
  'local-angle-frame':()=>idObj('local-angle-frame',label('angleFrame','Corner Frame'),t=>frame(t,'『','』')),
  'local-double-angle':()=>idObj('local-double-angle',label('doubleAngle','Double Angle'),t=>frame(t,'《','》')),
  'local-khmer-frame':()=>idObj('local-khmer-frame',label('khmerFrame','Ornate Frame'),t=>frame(t,'꧁','꧂')),
  'local-lotus-frame':()=>idObj('local-lotus-frame',label('lotusFrame','Lotus Frame'),t=>frame(t,'༺','༻')),
  'local-wing-frame':()=>idObj('local-wing-frame',label('wingFrame','Wing Frame'),t=>frame(t,'𓆩','𓆪')),
  'local-crown-frame':()=>idObj('local-crown-frame',label('crownFrame','Crown Frame'),t=>frame(t,'♛ ',' ♛')),
  'local-flower-frame':()=>idObj('local-flower-frame',label('flowerFrame','Flower Frame'),t=>frame(t,'✿ ',' ✿')),
  'local-wave-frame':()=>idObj('local-wave-frame',label('waveFrame','Wave Frame'),t=>frame(t,'〜','〜')),
  'local-circle-frame':()=>idObj('local-circle-frame',label('circleFrame','Circle Frame'),t=>frame(t,'○ ',' ○')),
  'local-diamond-frame':()=>idObj('local-diamond-frame',label('diamondFrame','Diamond Frame'),t=>frame(t,'◇ ',' ◇')),
  'local-music-frame':()=>idObj('local-music-frame',label('musicFrame','Music Frame'),t=>frame(t,'♪ ',' ♪')),
  'local-arrow-frame':()=>idObj('local-arrow-frame',label('arrowFrame','Arrow Frame'),t=>frame(t,'→ ',' ←')),
  'local-reverse':()=>idObj('local-reverse',label('reverse','Reverse'),t=>graphemes(t).reverse().join('')),
  'local-cursed':()=>idObj('local-cursed',label('cursed','Cursed Light'),cursedLight),
  'local-ru-quote':()=>idObj('local-ru-quote',label('ruQuote','« Russian Frame »'),t=>frame(t,'«','»')),
  'local-jp-hira-kata':()=>idObj('local-jp-hira-kata',label('hiraToKata','Hiragana → Katakana'),hiraToKata),
  'local-jp-kata-hira':()=>idObj('local-jp-kata-hira',label('kataToHira','Katakana → Hiragana'),kataToHira),
  'local-jp-half-kata':()=>idObj('local-jp-half-kata',label('halfKata','Halfwidth Katakana'),toHalfKata),
  'local-jp-quote':()=>idObj('local-jp-quote',label('jpQuote','Japanese Quote'),t=>frame(t,'「','」')),
  'local-jp-tortoise':()=>idObj('local-jp-tortoise',label('jpTortoise','Japanese Brackets'),t=>frame(t,'〔','〕')),
  'local-jp-white':()=>idObj('local-jp-white',label('jpWhite','White Brackets'),t=>frame(t,'〖','〗')),
  'local-thai-digits':()=>idObj('local-thai-digits',label('thaiDigits','Thai Digits'),thaiDigits),
  'local-thai-orb':()=>idObj('local-thai-orb',label('thaiOrb','Thai Frame'),t=>frame(t,'๏ ',' ๏')),
  'local-thai-end':()=>idObj('local-thai-end',label('thaiEnd','Thai End Frame'),t=>frame(t,'๛ ',' ๛')),
  'local-thai-decor':()=>idObj('local-thai-decor',label('thaiDecor','Thai Decorative Frame'),t=>frame(t,'๚ ',' ๚'))
};}

function fsdIndianDigits(text){const d={'0':'०','1':'१','2':'२','3':'३','4':'४','5':'५','6':'६','7':'७','8':'८','9':'९'};return Array.from(String(text)).map(c=>d[c]||c).join('');}
function fsdExtraAdditionFactories(){return {
  'local-in-danda':()=>idObj('local-in-danda',label('inDanda','Danda Frame'),t=>frame(t,'॥ ',' ॥')),
  'local-in-om':()=>idObj('local-in-om',label('inOm','Om Frame'),t=>frame(t,'ॐ ',' ॐ')),
  'local-in-digits':()=>idObj('local-in-digits',label('inDigits','Devanagari Digits'),fsdIndianDigits),
  'local-zh-corner':()=>idObj('local-zh-corner',label('zhCorner','Chinese Quote'),t=>frame(t,'「','」')),
  'local-zh-double':()=>idObj('local-zh-double',label('zhDouble','Double Chinese Quote'),t=>frame(t,'『','』')),
  'local-zh-book':()=>idObj('local-zh-book',label('zhBook','Book-title Frame'),t=>frame(t,'《','》')),
  'local-zh-white':()=>idObj('local-zh-white',label('zhWhite','White Brackets'),t=>frame(t,'〖','〗')),
  'local-zh-tortoise':()=>idObj('local-zh-tortoise',label('zhTortoise','Tortoise Brackets'),t=>frame(t,'〔','〕'))
};}

function additionIdsForMarket(m){
  if(m==='ru')return NATIVE_RU.slice();
  if(m==='ja')return NATIVE_JA.slice();
  if(m==='th')return NATIVE_TH.slice();
  if(m==='in')return NATIVE_IN.slice();
  if(m==='zh-TW')return NATIVE_ZH.slice();
  if(m==='it'||m==='pl'||m==='nl')return EXTENDED_LATIN.slice();
  return COMMON_LATIN.slice();
}
function makeAdditions(m){
  const f=Object.assign(allAdditionFactories(),fsdExtraAdditionFactories()),ids=additionIdsForMarket(m),out=[];
  for(const id of ids)if(f[id])out.push(f[id]());
  return out;
}
function keyOf(font){return font&&font.fsdMarketId?font.fsdMarketId:String(font&&font.name||'');}
function reorderInPlace(arr,priority){
  const map=new Map();for(const f of arr){map.set(keyOf(f),f);if(f&&f.name&&!map.has(f.name))map.set(f.name,f);}
  const used=new Set(),out=[];
  for(const k of priority||[]){const f=map.get(k);if(f&&!used.has(f)){used.add(f);out.push(f);}}
  for(const f of arr)if(!used.has(f)){used.add(f);out.push(f);}
  arr.splice(0,arr.length,...out);return arr;
}
function wrapCore(arr){
  for(const f of arr){if(!f||f._fsdLocal||typeof f.fn!=='function')continue;if(!f._fsdOriginalFn)try{Object.defineProperty(f,'_fsdOriginalFn',{value:f.fn,configurable:true});}catch(_){}f.fn=accentAware(f.fn);}
}
function updateVisibleCount(scope,count){
  try{
    if(scope==='quick'){
      const el=document.getElementById('fsd-quick-font-count');
      if(el)el.textContent="{n} czcionek i stylów tekstu • wpisz tekst, aby zobaczyć i wybrać".replace('{n}',count);
    }else if(scope==='writer'){
      const badge=document.getElementById('tw-font-badge');
      if(badge)badge.textContent=count+' stylów';
      const title=document.getElementById('tw-fonts-modal-title');
      if(title)title.textContent=count+' STYLÓW CZCIONEK';
    }
  }catch(_){}
}
function apply(arr,opts){
  opts=opts||{};if(!Array.isArray(arr))return arr;
  const scope=opts.scope||'unknown';
  if(arr._fsdMarketEnhanced===VERSION+'|'+MARKET+'|'+scope)return arr;
  const before=arr.length;
  wrapCore(arr);
  let additions=[];
  // Aesthetic/Game engine keeps only core transformations to avoid double decoration.
  if(scope!=='game' && opts.additions!==false){
    additions=makeAdditions(MARKET);
    const existing=new Set(arr.map(keyOf));
    additions=additions.filter(x=>!existing.has(keyOf(x)));
    arr.push(...additions);
  }
  const explicit=(LOCAL_PRIORITY[MARKET]||CORE_PRIORITY[MARKET]||[]);const addIds=additions.map(x=>x.fsdMarketId).filter(id=>!explicit.includes(id));const priority=explicit.concat(addIds,CORE_PRIORITY[MARKET]||[]);
  reorderInPlace(arr,priority);
  try{Object.defineProperty(arr,'_fsdMarketEnhanced',{value:VERSION+'|'+MARKET+'|'+scope,configurable:true});}catch(_){}
  arraysByScope[scope]=arr;
  updateVisibleCount(scope,arr.length);
  records.push({scope,market:MARKET,before,after:arr.length,additions:additions.map(x=>({id:x.fsdMarketId,name:x.name})),top:arr.slice(0,35).map(x=>({id:x.fsdMarketId||null,name:x.name}))});
  return arr;
}
function coverage(scope,text){
  const arr=arraysByScope[scope]||[];const chars=Array.from(String(text)).filter(ch=>LETTER_OR_NUMBER.test(ch));
  const rows=arr.map((f,i)=>{let changed=0,out='';try{out=f.fn(String(text));}catch(_){out=String(text);}for(const ch of chars){try{if(f.fn(ch)!==ch)changed++;}catch(_){}}return {i,id:f.fsdMarketId||null,name:f.name,out,coverage:chars.length?changed/chars.length:1,changed:out!==String(text)};});
  return rows;
}
function diagnostics(){return {version:VERSION,market:MARKET,records:records.map(r=>JSON.parse(JSON.stringify(r))),scopes:Object.keys(arraysByScope)};}
window.FSDMarketFonts={version:VERSION,market:MARKET,detectMarket,apply,coverage,diagnostics,getScope:s=>arraysByScope[s]||[],accentAware,graphemes};
try{document.documentElement.dataset.fsdMarket=MARKET;}catch(_){}
})();
