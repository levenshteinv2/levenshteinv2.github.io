"""Rebuild deterministic Japanese OFL fonts from pinned source; fresh QA required."""
import hashlib,json,subprocess,sys,urllib.request
from pathlib import Path
from fontTools.ttLib import TTFont
root=Path(sys.argv[1]); root.mkdir(parents=True,exist_ok=True)
rev="b46ed7e334ae7aaf3c6b9c446e087d57de39ff7d"
rows=[["kleeone","KleeOne-Regular.ttf","Klee One",400,"106bd3dbcfb24f7c971b761d63223b37104d4b6f"],["yomogi","Yomogi-Regular.ttf","Yomogi",400,"9ed46e0cdfe749a01ee2bee03852bf39cfcf7c65"],["zenkurenaido","ZenKurenaido-Regular.ttf","Zen Kurenaido",400,"306f69461d53039c2595f75891dd8a60be2dd65e"],["yuseimagic","YuseiMagic-Regular.ttf","Yusei Magic",400,"76e228f8f4cb429e1dc843f461fece77dddb8a49"],["hachimarupop","HachiMaruPop-Regular.ttf","Hachi Maru Pop",400,"1339bf206111860f1d3867146aa53662bdbd1919"],["yujisyuku","YujiSyuku-Regular.ttf","Yuji Syuku",400,"8a7db48fbf431ea97f14bedf6a4f5472347ab8a0"],["kaiseitokumin","KaiseiTokumin-Regular.ttf","Kaisei Tokumin",400,"23eadaffb59695aea3409ac5945b7beea3f24ed6"],["kaiseidecol","KaiseiDecol-Medium.ttf","Kaisei Decol",500,"79260a555e0d11b9439844f673f89484463fa057"]]
def sha(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def fetch(path):
    url=f"https://raw.githubusercontent.com/google/fonts/{rev}/ofl/{path}"
    with urllib.request.urlopen(url,timeout=30) as r:return r.read()
from concurrent.futures import ThreadPoolExecutor
sample="東京さくらカタカナ漢字ABC123"
def prepare(row):
    key,name,family,weight,expected=row
    data=fetch(key+"/"+name)
    assert sha(data)==expected,(key,sha(data))
    from io import BytesIO
    font=TTFont(BytesIO(data), recalcTimestamp=False)
    missing=[c for c in sample if ord(c) not in font.getBestCmap()]
    assert not missing,(family,missing)
    font.flavor="woff2"
    dest=root/(key+".woff2");font.save(dest)
    lic=fetch(key+"/OFL.txt");assert b"SIL OPEN FONT LICENSE" in lic
    (root/(key+"-OFL.txt")).write_bytes(lic)
    return {"family":family,"source_revision":rev,"source_blob":expected,"weight":weight,"bytes":dest.stat().st_size,"woff2_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"woff2_git_blob":sha(dest.read_bytes()),"sample_missing":missing}
with ThreadPoolExecutor(max_workers=3) as pool:
    report=list(pool.map(prepare,rows))
(root/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("JA_FONT_CMAP",len(report),"PASS")

assert len(report)==8 and all(not row['sample_missing'] for row in report)
