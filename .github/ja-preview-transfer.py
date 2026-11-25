"""Prepare exact Japanese font assets; verify original Git blob identity and glyph coverage."""
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
    font=TTFont(BytesIO(data))
    missing=[c for c in sample if ord(c) not in font.getBestCmap()]
    assert not missing,(family,missing)
    font.flavor="woff2"
    dest=root/(key+".woff2");font.save(dest)
    lic=fetch(key+"/OFL.txt");assert b"SIL OPEN FONT LICENSE" in lic
    (root/(key+"-OFL.txt")).write_bytes(lic)
    return {"family":family,"source_revision":rev,"source_blob":expected,"weight":weight,"bytes":dest.stat().st_size,"woff2_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"sample_missing":missing}
with ThreadPoolExecutor(max_workers=3) as pool:
    report=list(pool.map(prepare,rows))
(root/"manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf8")
print("JA_FONT_CMAP",len(report),"PASS")

expected={"kleeone.woff2":"c19d6b95b921f244513e40772130705c1766108c","yomogi.woff2":"5d7c90e8462ce9875d662e2021ea663a1fa2a29f","zenkurenaido.woff2":"deaf059eba9af2fa036520de2b3ecdab9352f350","yuseimagic.woff2":"4fc28957960eee7eea7d363c7bfbbd5a4ed84afd","hachimarupop.woff2":"0d470c5b367ba59debd9ffb917938ff024c741dc","yujisyuku.woff2":"3974ca3603a1a816b8e8d3e45b926525d90c0df8","kaiseitokumin.woff2":"2c31c3069588abc695f7a157ccd38420cf6e6657","kaiseidecol.woff2":"922355d8d893fbfed597fbd9967fa093ed111211","kleeone-OFL.txt":"cb9ced3f0aad10958824080d84c391100bc53986","yomogi-OFL.txt":"2987e11ede14be2802b5b33a63e5e55f7cd77160","zenkurenaido-OFL.txt":"e2eab0f7ab46b90817d72fbd6d8f7764b3bed6f0","yuseimagic-OFL.txt":"2e231ec4688fbfeb3eb071682f1f70dddea100d3","hachimarupop-OFL.txt":"6a4c49354dcd5ad707eac83a8be787c10221db59","yujisyuku-OFL.txt":"cff4fd743037483847e8d10afbc7ebc5e9226553","kaiseitokumin-OFL.txt":"60ad1b2898d1e02903ea7f55380b5a9ce30cee77","kaiseidecol-OFL.txt":"60ad1b2898d1e02903ea7f55380b5a9ce30cee77","manifest.json":"fab22ee81a5a0fb6cd3fb00e7df6e1b6c016ad57"}
for name,want in expected.items():
    actual=sha((root/name).read_bytes())
    assert actual==want,(name,actual,want)
print("JA_PREVIEW_EXACT_FONT_BLOBS",len(expected),"PASS")
