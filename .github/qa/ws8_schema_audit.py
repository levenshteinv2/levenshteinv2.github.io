"""WS8 offline structural audit. Run from repository root: python .github/qa/ws8_schema_audit.py"""
import collections, json, re, pathlib, html
from html.parser import HTMLParser
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False); self.canonical=[]; self.scripts=[]; self.buf=None; self.links=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="link" and "canonical" in a.get("rel","").split(): self.canonical.append(a.get("href"))
        if tag=="script" and a.get("type","").lower()=="application/ld+json": self.buf=[]
        if tag=="a" and a.get("href"): self.links.append(a["href"])
    def handle_data(self,data):
        if self.buf is not None: self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self.buf is not None: self.scripts.append("".join(self.buf)); self.buf=None
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)
def types(n):
    t=n.get("@type",[])
    return [t] if isinstance(t,str) else t
def page_type(n): return any(t.endswith("Page") for t in types(n))
root=pathlib.Path(".")
paths=json.loads((root/".github/qa/pages.json").read_text())
assert len(paths)==len(set(paths))==91
records=[]; definitions=collections.defaultdict(list); primaries=collections.defaultdict(set)
for path in paths:
    parser=Page(); parser.feed((root/path).read_text(encoding="utf-8-sig"))
    rec={"path":path,"canonical":parser.canonical,"errors":[],"nodes":[],"refs":[],"home_node":False}
    if len(parser.canonical)!=1: rec["errors"].append("canonical_count")
    for i,s in enumerate(parser.scripts):
        try: j=json.loads(s)
        except ValueError as e: rec["errors"].append(f"invalid_json_{i}: {e}"); continue
        nodes=j.get("@graph",[j]) if isinstance(j,dict) else j
        if not isinstance(nodes,list): rec["errors"].append("invalid_graph"); continue
        rec["nodes"].extend(n for n in nodes if isinstance(n,dict))
    if not parser.scripts: rec["errors"].append("no_jsonld")
    url=parser.canonical[0] if len(parser.canonical)==1 else None
    own=[n for n in rec["nodes"] if page_type(n) and n.get("url")==url]
    rec["primary_page_ids"]=[n.get("@id") for n in own]
    if not own: rec["errors"].append("no_canonical_page_node")
    if len(own)>1: rec["errors"].append("multiple_canonical_page_nodes")
    if url:
        for n in own:
            if isinstance(n.get("@id"),str): primaries[url].add(n["@id"])
    for n in walk(rec["nodes"]):
        ident=n.get("@id")
        if not isinstance(ident,str): continue
        if len(n)==1: rec["refs"].append(ident)
        elif "@type" in n: definitions[ident].append((path,types(n)))
    rec["home_node"]=path!="index.html" and any(n.get("@id")=="https://www.levenshtein.net/#webpage" for n in rec["nodes"])
    records.append(rec)
for rec in records:
    rec["unresolved_local_refs"]=sorted({r for r in rec["refs"] if r.startswith("https://www.levenshtein.net/") and r not in definitions})
    rec["has_part_id_mismatches"]=[]
    for n in rec["nodes"]:
        if n.get("@id") not in rec["primary_page_ids"]: continue
        hp=n.get("hasPart",[])
        if isinstance(hp,dict): hp=[hp]
        for part in hp if isinstance(hp,list) else []:
            if not isinstance(part,dict): continue
            i=part.get("@id","")
            if not isinstance(i,str): continue
            u=i.split("#")[0]
            if u in primaries and i not in primaries[u]: rec["has_part_id_mismatches"].append({"actual":i,"expected":sorted(primaries[u])})
    del rec["nodes"]; del rec["refs"]
report={"scope":len(paths),"pages_with_errors":sum(bool(r["errors"]) for r in records),"home_node_pages":[r["path"] for r in records if r["home_node"]],"unique_defined_ids":len(definitions),"unresolved_refs_are_review_candidates_not_automatic_errors":True,"pages":records}
print(json.dumps(report,indent=2,ensure_ascii=False))
