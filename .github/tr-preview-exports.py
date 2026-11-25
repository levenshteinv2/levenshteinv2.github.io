"""Read every delivered format and check the actual document or pixel content."""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageStat
from pypdf import PdfReader

root=Path(sys.argv[1])
results=[]
def check(name,inspect):
    file=root/name
    result={"file":name}
    try:
        data=file.read_bytes()
        result.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),details=inspect(data),status="PASS")
    except Exception as exc:
        result.update(status="FAIL",reason=str(exc))
    results.append(result)

def pixels(data):
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        assert im.format=="PNG"
        assert min(im.size)>=480
        spread=ImageStat.Stat(im.convert("RGB").resize((150,150))).stddev
        assert max(spread)>3, "blank image"
        return {"size":list(im.size),"format":"PNG","maxChannelStdDev":round(max(spread),2)}

def pdf(data):
    reader=PdfReader(io.BytesIO(data),strict=True)
    assert len(reader.pages)>=2,"not multipage"
    sizes=[]
    for page in reader.pages:
        images=list(page.images)
        assert images
        image=images[0].image
        assert image and min(image.size)>=480
        assert max(ImageStat.Stat(image.convert("RGB").resize((150,150))).stddev)>2
        sizes.append(list(image.size))
    return {"pages":len(reader.pages),"decodedRasterDimensions":sizes}

def docx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        for name in ("[Content_Types].xml","_rels/.rels","word/document.xml"):
            ET.fromstring(z.read(name))
        root=ET.fromstring(z.read("word/document.xml"))
        ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        lines=[p.text for p in root.findall(".//w:t",ns)]
        expected=[f"Satır {i} — İstanbul, ışık, şeker 2026" for i in range(1,56)]
        assert lines==expected,"Word XML differs from the 55 original lines"
        return {"paragraphs":len(lines),"first":lines[0],"last":lines[-1],"zipCRC":"OK"}

def carousel(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        names=z.namelist()
        assert len(names)>=2 and all(n.endswith(".png") for n in names)
        images=[pixels(z.read(n)) for n in names]
        assert len(set(hashlib.sha256(z.read(n)).digest() for n in names))==len(names)
        return {"members":names,"sizes":[im["size"] for im in images],"zipCRC":"OK"}

for name in ["certificate.png","social.png","handwriting.png"]:check(name,pixels)
for name in ["handwriting.pdf","styled.pdf"]:check(name,pdf)
check("doc.docx",docx)
check("carousel.zip",carousel)
(root/"file-integrity.json").write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding="utf-8")
print([(r["file"],r["status"],r.get("reason","")) for r in results])
sys.exit(any(r["status"]!="PASS" for r in results))
