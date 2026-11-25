"""Read-only DOI reconciliation against Crossref. Never edits the website."""
import collections, json, pathlib, re, time, unicodedata, urllib.error, urllib.parse, urllib.request
ROOT=pathlib.Path("site")
AUDIT=pathlib.Path(".github/knowledge-map/intelligence/ws8")
OUT=pathlib.Path("ws8-doi-report")
OUT.mkdir(exist_ok=True)
manifest=json.loads((ROOT/".github/qa/pages.json").read_text())
assert len(set(manifest))==len(manifest)==91
routes={("/" if p=="index.html" else "/"+p.removesuffix(".html")):p for p in manifest}
queue=json.loads((AUDIT/"external-reference-queue.json").read_text())
def doi(v):
    if not isinstance(v,str): return None
    m=re.match(r"^https?://(?:dx\.)?doi\.org/(.+)$",v,re.I)
    return urllib.parse.unquote(m[1]).lower().strip() if m else None
def normalize(s):
    return " ".join(re.findall(r"\w+",unicodedata.normalize("NFKC",str(s)).casefold()))
def walk(n):
    if isinstance(n,dict):
        yield n
        for v in n.values(): yield from walk(v)
    elif isinstance(n,list):
        for v in n: yield from walk(v)
refs=collections.defaultdict(set)
for x in queue:
    if x["route"] in routes and doi(x["target"]): refs[doi(x["target"])].add(routes[x["route"]])
nodes=collections.defaultdict(list)
for p in manifest:
    s=(ROOT/p).read_text(encoding="utf-8-sig")
    for m in re.finditer(r"""<script\b[^>]*type=["']application/ld\+json["'][^>]*>([\s\S]*?)</script>""",s,re.I):
        for n in walk(json.loads(m[1])):
            d=doi(n.get("@id")) or doi(n.get("url"))
            if d and n.get("@type"):
                nodes[d].append({"page":p,"name":n.get("name"),"headline":n.get("headline"),"datePublished":n.get("datePublished"),"author":n.get("author"),"type":n.get("@type")})
                refs[d].add(p)
def resolve(d):
    u="https://api.crossref.org/works/"+urllib.parse.quote(d,safe="")
    for attempt in range(3):
        try:
            req=urllib.request.Request(u,headers={"User-Agent":"Levenshtein.net WS8 bibliographic audit (https://github.com/levenshteinv2/levenshteinv2.github.io)","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=12) as f: return {"status":"resolved","data":json.load(f)["message"]}
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504): return {"status":"http_error","code":e.code}
            if attempt<2:
                try: delay=min(30,max(3,float(e.headers.get("Retry-After","5"))))
                except ValueError: delay=5
                time.sleep(delay)
        except (OSError,ValueError,KeyError) as e:
            if attempt==2: return {"status":"request_error","error":str(e)}
            time.sleep(3)
    return {"status":"retry_exhausted"}
def parts(m,k):
    v=m.get(k,{}).get("date-parts",[])
    return v[0] if v and v[0] else []
def compatible(s,dates):
    if not isinstance(s,str) or not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?",s): return None
    x=[int(y) for y in s.split("-")]
    return any(len(d)>=len(x) and d[:len(x)]==x for d in dates)
rows=[]
for i,d in enumerate(sorted(refs),1):
    time.sleep(1.1)
    r=resolve(d); row={"doi":d,"pages":sorted(refs[d]),"status":r["status"],"occurrences":nodes[d],"review":[]}
    if r["status"]=="resolved":
        m=r["data"]; titles=m.get("title",[]); date_fields={k:parts(m,k) for k in ("published","published-online","published-print","issued")}; date_fields={k:v for k,v in date_fields.items() if v}
        row["crossref"]={"doi":m.get("DOI"),"titles":titles,"dates":date_fields,"authors":[{"given":a.get("given"),"family":a.get("family"),"name":a.get("name")} for a in m.get("author",[])],"container":m.get("container-title",[]),"publisher":m.get("publisher"),"url":m.get("URL")}
        if str(m.get("DOI","")).lower()!=d: row["review"].append({"code":"doi_identity_mismatch"})
        for n in nodes[d]:
            for k in ("name","headline"):
                if n[k] and titles and not any(normalize(n[k])==normalize(t) for t in titles): row["review"].append({"page":n["page"],"code":"title_review","field":k,"value":n[k]})
            if n["datePublished"] and date_fields and compatible(n["datePublished"],list(date_fields.values())) is not True: row["review"].append({"page":n["page"],"code":"date_precision_or_value_review","value":n["datePublished"]})
            au=n["author"]; ca=m.get("author",[])
            if au and ca:
                local=au if isinstance(au,list) else [au]
                if len(local)!=len(ca): row["review"].append({"page":n["page"],"code":"author_count_review","local":len(local),"crossref":len(ca)})
                else:
                    for j,(a,b) in enumerate(zip(local,ca)):
                        lname=a.get("name") if isinstance(a,dict) else a
                        family=b.get("family")
                        if lname and family and normalize(family) not in normalize(lname): row["review"].append({"page":n["page"],"code":"author_name_review","index":j,"local":lname,"crossref_family":family})
        if not nodes[d]: row["review"].append({"code":"reference_only_no_typed_node"})
    else:
        row["error"]={k:v for k,v in r.items() if k!="status"}
    rows.append(row)
    (OUT/"results.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    if i%20==0: print(f"Progress {i}/{len(refs)}",flush=True)
summary={"scope":len(manifest),"unique_dois":len(refs),"processed":len(rows),"status_counts":dict(collections.Counter(x["status"] for x in rows)),"review_codes":dict(collections.Counter(y["code"] for x in rows for y in x["review"])),"typed_occurrences":sum(len(x["occurrences"]) for x in rows),"note":"Crossref metadata reconciliation only; review candidates are not proven errors. No HTML changes; no automated semantic certification."}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
