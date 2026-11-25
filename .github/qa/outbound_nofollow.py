"""Mandatory outbound nofollow gate; exact anchor-tag edits only."""
import argparse, collections, json, pathlib, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urlsplit
ROOT=pathlib.Path(".")
HOSTS={"levenshtein.net","www.levenshtein.net","levenshteinv2.github.io"}
ATTR=re.compile(r"""([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?""")
def external(href):
    u=urlsplit(href.strip())
    return (u.scheme.lower() in ("http","https") or (not u.scheme and bool(u.netloc))) and bool(u.hostname) and u.hostname.lower().rstrip(".") not in HOSTS
class Scan(HTMLParser):
    def __init__(self,s):
        super().__init__(convert_charrefs=False)
        self.line_starts=[0]
        for m in re.finditer("\n",s): self.line_starts.append(m.end())
        self.anchors=[]
        self.feed(s); self.close()
    def handle_starttag(self,tag,attrs):
        if tag not in ("a","area"): return
        if not any(k=="href" for k,v in attrs): return
        d=dict(attrs); raw=self.get_starttag_text()
        line,col=self.getpos()
        self.anchors.append((self.line_starts[line-1]+col,raw,attrs,d.get("href") or "",external(d.get("href") or "")))
def tokens(attrs):
    return set((dict(attrs).get("rel") or "").lower().split())
def patch(raw,attrs):
    # Scan after tag name, not inside quoted attribute values.
    start=re.match(r"<(?:a|area)\b",raw,re.I).end()
    rel=[m for m in ATTR.finditer(raw,start) if m.group(1).lower()=="rel"]
    assert len(rel)==sum(k=="rel" for k,v in attrs)<=1,raw
    if rel:
        m=rel[0]; value=next((v for v in m.groups()[1:] if v is not None),"")
        new='rel="'+(value+" nofollow").strip().replace('"',"&quot;")+'"'
        return raw[:m.start()]+new+raw[m.end():]
    i=len(raw)-1
    if raw[:i].endswith("/"): i-=1
    return raw[:i]+' rel="nofollow"'+raw[i:]
def run(s,fix):
    a=Scan(s).anchors
    changes=[]; missing=[]
    for pos,raw,attrs,h,ext in a:
        if ext and "nofollow" not in tokens(attrs):
            missing.append(h)
            if fix: changes.append((pos,raw,patch(raw,attrs)))
    t=s
    for pos,raw,new in reversed(changes):
        assert t[pos:pos+len(raw)]==raw
        t=t[:pos]+new+t[pos+len(raw):]
    b=Scan(t).anchors
    assert len(a)==len(b)
    for (_,raw,attrs,h,ext),(_,raw2,attrs2,h2,ext2) in zip(a,b):
        assert (h,ext)==(h2,ext2)
        if ext and fix:
            assert "nofollow" in tokens(attrs2)
            assert tokens(attrs)<=tokens(attrs2)
            assert [(k,v) for k,v in attrs if k!="rel"]==[(k,v) for k,v in attrs2 if k!="rel"]
        else: assert raw==raw2
    return t,{"external":sum(x[4] for x in a),"missing_before":len(missing),"changed_links":len(changes),"missing_after":sum(x[4] and "nofollow" not in tokens(x[2]) for x in b),"missing_examples":missing[:10]}
def selftest():
    s="""<a href="/x">internal</a><a href='https://www.levenshtein.net/x'>site</a><a HREF='//example.org' title='rel="fake"' rel='noopener noreferrer'>x</a><a href=https://example.org rel=ugc>x</a><a href="https://example.org">x</a><a href="mailto:foo@example.org">mail</a><script>var t='<a href="https://example.org">';</script><area href="https://example.org"/>"""
    t,r=run(s,True)
    assert r["external"]==4 and r["changed_links"]==4 and r["missing_after"]==0
    assert run(t,True)[0]==t
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--fix",action="store_true"); args=parser.parse_args()
    selftest()
    pages=json.loads((ROOT/".github/qa/pages.json").read_text())
    assert len(set(pages))==len(pages)==91
    rows=[]; pending=[]
    for p in pages:
        path=ROOT/p
        old=path.read_bytes().decode("utf-8")
        new,row=run(old,args.fix)
        rows.append(dict(page=p,**row))
        if old!=new: pending.append((path,new))
    if args.fix:
        for path,new in pending: path.write_bytes(new.encode("utf-8"))
        for path,new in pending: assert path.read_bytes().decode("utf-8")==new
    counts={k:sum(r[k] for r in rows) for k in ("external","missing_before","changed_links","missing_after")}
    report={"pages":len(rows),"changed_pages":len(pending),**counts,"scope":"HTML a/area http(s) or protocol-relative links in 91 knowledge source pages; not runtime-generated DOM links", "rows":rows}
    out=ROOT/"qa-report";out.mkdir(exist_ok=True)
    (out/"outbound-nofollow.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="rows"},ensure_ascii=False))
    if counts["missing_after"]: raise SystemExit(1)
if __name__=="__main__": main()
