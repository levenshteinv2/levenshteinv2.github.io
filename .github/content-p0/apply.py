import json,re,subprocess,hashlib,html
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit
BASE='f630405b639bf921160fbda5747ff940f48c2333'
R=Path('.github/content-p0')
routes=json.loads((R/'self-routes.json').read_text())
manifest=json.loads(Path('.github/qa/pages.json').read_text())
assert len(routes)==67 and len(set(routes))==67 and len(manifest)==91
files={r:r.lstrip('/')+'.html' for r in routes}
assert all(p in manifest for p in files.values())
allowed=set(files.values())|{'index.html','ukkonen-algorithm.html','translation-edit-rate-and-mt-evaluation.html'}
def replace_once(s,a,b):
    assert s.count(a)==1, a[:180]
    return s.replace(a,b,1)
def read(p):return Path(p).read_bytes().decode('utf-8')
def baseline(p):return subprocess.check_output(['git','show',BASE+':'+p]).decode('utf-8')
def soup(s):return BeautifulSoup(s,'html.parser')
def rel(s):
    x=soup(s).select_one('h2.lv-related-title + ol.lv-posts')
    return [a['href'] for a in x.select('li.lv-post h3.lv-post__title a[href]')] if x else []
def related_edit(s,r):
    pattern=r'(<h2 class="lv-related-title">Related Posts</h2>\s*<ol class="lv-posts">)([\s\S]*?)(</ol>)'
    matches=list(re.finditer(pattern,s));assert len(matches)==1,(r,len(matches))
    m=matches[0];li=re.compile(r'<li class="lv-post">[\s\S]*?</li>')
    items=list(li.finditer(m[2]));assert items,(r,'items')
    keep=[];removed=0
    for item in items:
        a=soup(item[0]).select_one('h3.lv-post__title a[href]');assert a
        if urlsplit(a['href']).path.rstrip('/')==r:
            removed+=1
        else:
            new=re.sub(r'(<span aria-hidden="true" class="lv-post__no">)\d+(</span>)',lambda x:x[1]+str(len(keep)+1).zfill(2)+x[2],item[0],count=1)
            keep.append(new)
    assert removed==1 and keep,(r,removed,len(keep))
    old=m[0];new=m[1]+'\n'+'\n'.join(keep)+'\n'+m[3]
    out=replace_once(s,old,new)
    assert rel(out)==[x for x in rel(s) if urlsplit(x).path.rstrip('/')!=r],r
    return out
compact="""function boundedDistance(x, y, k) {
    // x and y are arrays of sequence elements; k is a nonnegative integer.
    if (!Number.isSafeInteger(k) || k < 0 || k >= Number.MAX_SAFE_INTEGER)
        throw new RangeError("Invalid threshold");
    if (Math.abs(x.length - y.length) > k) return k + 1;
    const inf = k + 1;
    let prev = new Map();
    for (let j = 0; j <= Math.min(y.length, k); j++) prev.set(j, j);
    for (let i = 1; i <= x.length; i++) {
        const cur = new Map();
        for (let j = Math.max(0, i-k); j <= Math.min(y.length, i+k); j++) {
            const value = j === 0 ? i : Math.min(inf,
                (prev.get(j) ?? inf) + 1,
                (cur.get(j-1) ?? inf) + 1,
                (prev.get(j-1) ?? inf) + Number(x[i-1] !== y[j-1]));
            cur.set(j, value);
        }
        prev = cur;
    }
    return prev.get(y.length) ?? inf;
}"""
# The printed implementation is validated as emitted, not inferred from a prior prototype.
(R/'compact-band.mjs').write_text(compact+'\nexport { boundedDistance };\n',encoding='utf-8')
home_old='<p>The Levenshtein algorithm, also known as edit distance, measures the minimum number of edit operations required to transform one sequence into another. The standard operations are insertion, deletion, and substitution.</p>'
home_new='<p><strong>Levenshtein distance</strong> is the minimum number of single-element insertions, deletions, and substitutions needed to transform one sequence into another, with each operation costing one. Matching identical elements costs zero. It is one member of the broader family of <a href="/edit-distance">edit-distance models</a>. A Levenshtein algorithm computes this distance; the distance is the mathematical quantity, not a particular implementation.</p>'
ter_old='''<p>A plausible alignment contains:</p>
<pre>
approved -&gt; accepted    substitution
missing "the"           deletion relative to reference alignment
</pre>
<p>Using the usual hypothesis-to-reference edit terminology:</p>
<pre>
S = 1
D = 1
I = 0
Sh = 0
N = 5
</pre>'''
ter_new='''<p>To transform the hypothesis into the reference, replace <code>accepted</code> with <code>approved</code> and insert the missing <code>the</code> before <code>proposal</code>:</p>
<pre>
accepted -&gt; approved    substitution
insert "the"            insertion
</pre>
<p>For edits in this hypothesis-to-reference direction:</p>
<pre>
S = 1
D = 0
I = 1
Sh = 0
N = 5
</pre>
<p>Some reference-oriented error reports instead label a missing reference word as a deletion. State the direction when reporting individual edit counts; the total of two edits, and hence the TER, is unchanged in this example. See <a href="https://aclanthology.org/2006.amta-papers.25/">Snover et al. (2006), A Study of Translation Edit Rate with Targeted Human Annotation</a>.</p>'''
block='''<p><strong>Implementation cost:</strong> the dense-row reference listing clears all <code>n + 1</code> entries of the working array on every processed row. Although it evaluates only the active band, its full-row clearing alone can require Θ(mn) work for nonempty inputs of lengths m and n. The band-cell count is not the total running time of that listing.</p>
<p>A compact alternative stores only the active columns. For unit-cost global Levenshtein distance and a nonnegative integer threshold k, the following reference implementation returns the exact distance when it is at most k, and k + 1 otherwise. Inputs are arrays of sequence elements; choose the representation before calling it.</p>
<pre><code>'''+html.escape(compact,quote=False)+'''</code></pre>
<p>It visits at most (m + 1) · min(n + 1, 2k + 1) active states and stores at most two active rows. Under constant-time map access, this gives O((m + 1) · min(n + 1, 2k + 1)) time and O(min(n + 1, 2k + 1)) auxiliary space. This is an implementation example, not a new theorem about Ukkonen's original algorithm.</p>
<p><strong>Reproducible check:</strong> compare the returned value with min(full Wagner–Fischer distance, k + 1) for every ordered pair of binary strings of lengths 0–5, and each threshold from 0 to 6. This is 63 × 63 × 7 = 27,783 checks. In the compact-band prototype, equal strings of length 1,024 at k = 1 required 3,073 active-state writes (including the initial row), while clearing every dense working row requires 1,049,600 reset writes alone. These counts measure different, explicitly identified operations, not elapsed time or a speedup factor. Finite tests do not replace a proof.</p>
'''
results=[]
for p in manifest:
    old=read(p);assert old==baseline(p),(p,'baseline drift')
    new=old
    if p in files.values():
        r=next(r for r,f in files.items() if f==p)
        new=related_edit(new,r)
    if p=='index.html':new=replace_once(new,home_old,home_new)
    if p=='ukkonen-algorithm.html':
        new=replace_once(new,'<h2 id="ux-section-58">',block+'<h2 id="ux-section-58">')
    if p=='translation-edit-rate-and-mt-evaluation.html':new=replace_once(new,ter_old,ter_new)
    a,b=soup(old),soup(new)
    for sel in ['head','header','footer','link[rel=canonical]','meta[name=robots]','script[type="application/ld+json"]','h1']:
        assert [str(x) for x in a.select(sel)]==[str(x) for x in b.select(sel)],(p,sel)
    assert [x.get('id') for x in a.select('[id]')]==[x.get('id') for x in b.select('[id]')],(p,'ids')
    if p not in {'index.html','ukkonen-algorithm.html','translation-edit-rate-and-mt-evaluation.html'}:
        assert [str(x) for x in a.select('.article-body')]==[str(x) for x in b.select('.article-body')],(p,'body')
    if new!=old:
        assert p in allowed
        Path(p).write_bytes(new.encode('utf-8'))
        results.append(dict(path=p,sha_before=hashlib.sha256(old.encode()).hexdigest(),sha_after=hashlib.sha256(new.encode()).hexdigest(),related_before=len(rel(old)),related_after=len(rel(new))))
assert {x['path'] for x in results}==allowed
assert len(results)==68
# Protect entire tracked tree except reviewed pages and audit scripts.
changed=subprocess.check_output(['git','diff','--name-only',BASE]).decode().splitlines()
assert all(p in allowed or p.startswith('.github/content-p0/') or p=='.github/workflows/content-p0-staging.yml' for p in changed),changed
(R/'static-delta.json').write_text(json.dumps(dict(base=BASE,changed_pages=len(results),removed_self_cards=67,unchanged_knowledge_pages=91-len(results),results=results,gate='PASS',deployment='NONE'),indent=2)+'\n')
print('P0 delta PASS',len(results),'pages; 67 self cards removed')
