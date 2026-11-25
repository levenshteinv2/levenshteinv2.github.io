# Internal Link Graph — target policy and change candidates

Snapshot: 528b3f6539411d1629164ddd7460d6a4ac0fafb3

Củng cố entity; nối entity. This is the target **delta** against the observed graph, not a replacement graph. Preserve links unless explicitly reviewed. All edits remain unapproved for deployment.

## Relationship review

| Decision | Count |
|---|---:|
| retain_existing_relationship | 103 |
| retain_navigation_no_body_link | 77 |
| correct_audit_relationship | 5 |
| candidate_add_after_placement_qa | 18 |
| retain_directory_link_tool_boundary | 17 |

## Proposed links (placement QA required)

| Priority | Source | Target | Placement | Anchor hypothesis |
|---|---|---|---|---|
| P1 | /applications | /search | Applications intro | Search and Information Retrieval |
| P1 | /applications | /data-matching | Applications intro | Data Matching and Entity Resolution |
| P1 | /applications | /language-processing | Applications intro | Language Processing |
| P1 | /applications | /bioinformatics | Applications intro | Bioinformatics and Sequence Analysis |
| P1 | /applications | /coding-theory | Applications intro | Coding Theory and Synchronization Codes |
| P1 | /applications | /software-systems | Applications intro | Software Systems and Security |
| P1 | /edit-distance | / | ux-section-3 | Levenshtein distance |
| P2 | /approximate-string-matching | /fuzzy-search-with-edit-distance | ux-section-35 | fuzzy search with edit distance |
| P1 | /approximate-edit-distance-algorithms | /approximate-string-matching | ux-section-114 | approximate string matching |
| P1 | /wagner-fischer-algorithm | /paper-wagner-fischer-1974 | ux-section-89 | Wagner–Fischer’s 1974 paper |
| P1 | /ukkonen-algorithm | /paper-ukkonen-1985 | ux-section-3 | Ukkonen’s 1985 paper |
| P1 | /myers-bit-vector-algorithm | /paper-myers-1999 | ux-section-122 | Myers’s 1999 paper |
| P1 | /levenshtein-automata | /paper-schulz-mihov-2002 | ux-section-29 | Schulz–Mihov’s 2002 paper |
| P1 | /approximate-string-matching | /paper-navarro-2001 | ux-section-41 | analysis of Navarro’s 2001 survey |
| P1 | /edit-distance-complexity | /paper-backurs-indyk | ux-section-42 | Backurs–Indyk’s 2015 paper |
| P2 | /word-error-rate-and-asr-evaluation | /edit-operations | ux-section-2 | edit operations |
| P2 | /levenshtein_implementation.htm | /levenshtein-implementations | main legacy text | modern Levenshtein implementations |
| P2 | /levenshtein_search.htm | /fuzzy-search-with-edit-distance | main legacy text | fuzzy search with edit distance |

## Corrections to original audit graph

| Original relation | Actual relation | Evidence |
|---|---|---|
| /implementations → /indexing-and-filtering-for-edit-distance | /algorithms → /indexing-and-filtering-for-edit-distance | actual_parent_listing |
| /indexing-and-filtering-for-edit-distance → /implementations | /indexing-and-filtering-for-edit-distance → /algorithms | actual_breadcrumb |
| /language-processing → /spell-and-query-correction | /search → /spell-and-query-correction | actual_parent_listing |
| /spell-and-query-correction → /language-processing | /spell-and-query-correction → /search | actual_breadcrumb |
| /unicode-text-transformations → /text-tools | /unicode-text-transformations → /unicode-text-tools | actual_contextual |

## Structural policy

- Existing parent-child navigation stays; no forced body backlink to hub.
- Applications should expose its six domain hubs in main content, retaining existing article discoverability.
- Algorithms owns the Indexing article's current breadcrumb; Search owns Spell & Query Correction. Secondary topical association stays possible without moving pages.
- Unicode transformations → Styled Unicode → Unicode Text Tools; Text Tools remains utility parent, not a subtype of an algorithm.
- 17 tool directory links remain untouched. Snapshot mixed 7 Preview and 10 production read-only tools.
- Preserve original external DOI and scholarly references.

Full existing graph audit and semantic deployment gate remain pending.
