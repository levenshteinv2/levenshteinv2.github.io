"""Scoped final V2 shell migration. Preserve every script and tool subtree byte."""
from pathlib import Path
import re,json,hashlib,html
from urllib.parse import urlsplit
R=Path(".")
routes=[
("fancy-text-generator","en-US","US","Fancy Text Generator"),("schriftgenerator","de-DE","DE","Schriftgenerator"),("generador-de-letras","es-ES","ES","Generador de Letras"),("letras-diferentes","pt-BR","BR","Letras Diferentes"),("font-henkan","ja-JP","JP","フォント変換"),("krasivyy-shrift","ru-RU","RU","Красивый шрифт"),("ki-tu-dac-biet","vi-VN","VN","Font Chữ Đẹp"),("letras-bonitas","es-MX","MX","Letras Bonitas"),("yazi-stilleri","tr-TR","TR","Yazı Stilleri"),("font-style","en-IN","IN","Font Style"),("te-shu-zi-ti","zh-Hant-TW","TW","特殊字體"),("caratteri-speciali","it-IT","IT","Caratteri Speciali"),("akson-phiset","th-TH","TH","อักษรพิเศษ"),("font-aesthetic","id-ID","ID","Font Aesthetic"),("lettertypes","nl-NL","NL","Lettertypes"),("police-d-ecriture","fr-FR","FR","Police d’Écriture"),("generator-czcionek","pl-PL","PL","Generator Czcionek")]
lookup={x[0]:x for x in routes}
def read(p):return p.read_bytes().decode("utf8")
def sha(s):return hashlib.sha256(s.encode("utf8")).hexdigest()
def scripts(s):return re.findall(r"<script\b[^>]*>[\s\S]*?</script\s*>",s,re.I)
def meta(s):return re.findall(r'<(?:meta|link|title)\b[^>]*>(?:[^<]*</title>)?',s[:s.lower().index("</head>")],re.I)
def links(s):
    def fix(m):
        u=m.group(2);v=urlsplit(u);slug=v.path.strip("/").removesuffix(".html")
        if v.netloc not in ("","www.levenshtein.net","levenshtein.net") or slug not in lookup:return m.group()
        if not v.path.startswith("/") and v.netloc:return m.group()
        return m.group(1)+'/'+slug+('?' + v.query if v.query else '')+('#'+v.fragment if v.fragment else '')+m.group(3)
    # Anchors only; never canonical, schema, scripts or tool internals.
    return re.sub(r'(<a\b[^>]*?\bhref=["\'])([^"\']+)(["\'])',fix,s,flags=re.I)
def menu(current="",all_label="All text tools",unicode_label="Unicode text tools"):
    a='<div class="ux-tool-menu"><div class="ux-tool-menu-hubs"><a href="/text-tools">'+html.escape(all_label)+'</a><a href="/unicode-text-tools">'+html.escape(unicode_label)+'</a></div><div class="ux-tool-menu-grid">'
    for slug,lang,region,name in routes:
        cur=' aria-current="page"' if slug==current else ''
        a+=f'<a href="/{slug}" lang="{lang}"{cur}><span class="ux-market">{region}</span><span>{html.escape(name)}</span></a>'
    return a+"</div></div>"
# Local labels for new shell navigation only. Existing titles and editorial text unchanged.
labels={
"en-US":("Research","All text tools","Unicode text tools","Skip to content"),"en-IN":("Research","All text tools","Unicode text tools","Skip to content"),
"de-DE":("Forschung","Alle Textwerkzeuge","Unicode-Textwerkzeuge","Zum Inhalt"),"es-ES":("Investigación","Todas las herramientas","Herramientas Unicode","Ir al contenido"),"es-MX":("Investigación","Todas las herramientas","Herramientas Unicode","Ir al contenido"),
"pt-BR":("Pesquisa","Todas as ferramentas","Ferramentas Unicode","Ir para o conteúdo"),"ja-JP":("研究","すべての文字ツール","Unicode文字ツール","本文へ移動"),"ru-RU":("Исследования","Все инструменты","Инструменты Unicode","К содержанию"),
"vi-VN":("Nghiên cứu","Tất cả công cụ","Công cụ Unicode","Đến nội dung"),"tr-TR":("Araştırma","Tüm metin araçları","Unicode araçları","İçeriğe geç"),"zh-Hant-TW":("研究","所有文字工具","Unicode 文字工具","跳至內容"),
"it-IT":("Ricerca","Tutti gli strumenti","Strumenti Unicode","Vai al contenuto"),"th-TH":("งานวิจัย","เครื่องมือทั้งหมด","เครื่องมือ Unicode","ข้ามไปยังเนื้อหา"),"id-ID":("Riset","Semua alat teks","Alat Unicode","Lewati ke konten"),
"nl-NL":("Onderzoek","Alle teksttools","Unicode-teksttools","Naar inhoud"),"fr-FR":("Recherche","Tous les outils","Outils Unicode","Aller au contenu"),"pl-PL":("Badania","Wszystkie narzędzia","Narzędzia Unicode","Przejdź do treści")}
def tool_header(s,slug):
    m=re.search(r'<header id="lvt-site-header">[\s\S]*?</header>',s);assert m,slug
    nav=re.search(r'<nav class="lvt-desktop" aria-label="([^"]+)">([\s\S]*?)</nav>',m.group());assert nav,slug
    items=re.findall(r'<a href="([^"]+)">([\s\S]*?)</a>',nav[2]);assert len(items)==4,(slug,items)
    lang=lookup[slug][1];research,all_label,unicode_label,skip=labels[lang]
    def a(i):return '<a href="'+items[i][0]+'">'+items[i][1]+'</a>'
    # Retain native navigation labels; the research pages are English.
    return '<header id="lvt-site-header" class="ux-header ux-tool-header"><a class="ux-skip" href="#lvt-main">'+skip+'</a><div class="ux-nav"><a class="ux-brand" href="/">Levenshtein.net</a><nav class="ux-primary" aria-label="'+nav[1]+'">'+a(0)+a(2)+a(3)+'<details name="ux-primary-menu"><summary>'+research+'</summary><div class="ux-drop">'+a(0)+a(2)+a(3)+'<a href="/foundations" lang="en">Foundations</a><a href="/algorithms" lang="en">Algorithms</a><a href="/applications" lang="en">Applications</a></div></details><details name="ux-primary-menu" class="ux-tool-dropdown"><summary>'+items[1][1]+'</summary>'+menu(slug,all_label,unicode_label)+'</details></nav></div></header>'
def core(s):
    start=s.index('<div id="lf194-root"')
    end=s.index('<article id="lvt-article"',start)
    return s[start:end]
def change_tool(s,slug):
    old=s
    c=core(s)
    s,n=re.subn(r'<body style="margin:0;background:#faf9f6">','<body class="ux-tool-page" style="margin:0;background:#f4f7fb">',s,count=1);assert n==1
    s,n=re.subn(r'<header id="lvt-site-header">[\s\S]*?</header>',lambda _:tool_header(old,slug),s,count=1);assert n==1
    s=s.replace('<main id="lvt-main">','<main id="lvt-main" tabindex="-1">',1)
    s,n=re.subn(r'</head>', '<link rel="stylesheet" href="/assets/knowledge/tool-shell.css"></head>',s,count=1,flags=re.I);assert n==1
    # Normalize only links in editorial article, not engine or generated DOM.
    s,n=re.subn(r'<article id="lvt-article"[\s\S]*?</article>',lambda m:links(m.group()),s,count=1);assert n==1
    assert core(s)==c and scripts(s)==scripts(old),slug
    assert meta(s)[:-1]==meta(old),slug
    return s,sha(c)
def knowledge(s):
    before=s
    # Shield every script (including schema) during scoped link normalization.
    chunks=re.split(r'(<script\b[^>]*>[\s\S]*?</script\s*>)',s,flags=re.I)
    for i in range(0,len(chunks),2):chunks[i]=links(chunks[i])
    s="".join(chunks)
    pattern=r'<details name="ux-primary-menu"><summary>Text Tools</summary><div class="ux-drop">[\s\S]*?</div></details>'
    s,n=re.subn(pattern,lambda _: '<details name="ux-primary-menu" class="ux-tool-dropdown"><summary>Text Tools</summary>'+menu()+'</details>',s)
    assert n<=1
    assert scripts(s)==scripts(before) and meta(s)==meta(before)
    return s
rows=[]
for p in sorted(R.glob("*.html")):
    s=read(p);slug=p.stem
    if slug in lookup:
        new,ch=change_tool(s,slug);kind="tool-shell"
    else:
        new=knowledge(s);ch=None;kind="navigation-only"
    if new!=s:
        p.write_bytes(new.encode("utf8"));rows.append({"path":p.name,"before":sha(s),"after":sha(new),"kind":kind,"core_sha256":ch})
assert sum(x["kind"]=="tool-shell" for x in rows)==17
for slug in ["text-tools","unicode-text-tools"]:
    s=read(R/(slug+".html"))
    assert len(re.findall(r'class="lv-tool-card"',s))==17
    assert all(f'href="/{x[0]}"' in s for x in routes)
    # Distinguish region badges while preserving native descriptions.
    def card(m):
        a=m.group();url=re.search(r'href="/([^"]+)"',a)
        if not url or url[1] not in lookup:return a
        lang,region=lookup[url[1]][1:3]
        a=re.sub(r'(<span aria-hidden="true" class="lv-lang-badge[^"]*">)[^<]*(</span>)',lambda x:x[1]+region+x[2],a,count=1)
        return a
    p=R/(slug+".html");new=re.sub(r'<a\b[^>]*class="lv-tool-card"[\s\S]*?</a>',card,s)
    p.write_bytes(new.encode("utf8"))
    row=next(x for x in rows if x["path"]==p.name);row["after"]=sha(new)
Path("qa/shell-v2").mkdir(parents=True,exist_ok=True)
Path("qa/shell-v2/manifest.json").write_text(json.dumps(rows,indent=2))
print("SHELL_MIGRATED",len(rows),"17 immutable tool cores")
