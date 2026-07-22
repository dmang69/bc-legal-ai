---
name: legal-file-assistant
description: >
  Combined Canadian court document downloader AND Windows local file search.
  Aliases: court-downloader, file-search, legal-file-assistant, boa-downloader.
  TRIGGER court download: "download this case", "get me the PDF of", "pull this judgment",
  "build my BOA", "retrieve this authority", or any Canadian citation (SCC/SCR/BCCA/BCSC/FCA/CanLII).
  TRIGGER local search: "find my file", "search for", "where is my", "locate the PDF of",
  "find all my court documents", "find anything modified last week", "search inside my documents",
  "find duplicates", "export my file list", or any request to locate files/folders on Windows.
  BOTH modes when needed e.g. "download Vavilov and find where I saved the old copy".
  Lawful public sources only; no Cloudflare bypass; no sealed records; no System32 search.
---

# Legal Assistant — Court Document Downloader + Windows File Search

One skill, two engines. **Lawful access only.**

**Not legal advice.** Official PDFs and currency must be verified by counsel before filing. BOA merges are working drafts.

## Scripts (run from monorepo)

```text
skills/legal-file-assistant/scripts/
  court_engine.py   # SCC download + reference PDF fallback
  file_engine.py    # Windows file search + duplicates
  boa_assembler.py  # optional PDF merge
  cli.py            # unified CLI
references/scc-item-ids.md
outputs/            # default write location for downloads/reports
```

```powershell
cd C:\Users\Dizzle\projects\bc-legal-ai\skills\legal-file-assistant\scripts
python cli.py download --citation "2019 SCC 65" --out ..\outputs
python cli.py search --query "vavilov" --ext .pdf
python cli.py both --citation "2019 SCC 65" --query vavilov
```

## Mode detection

| User says | Mode |
|-----------|------|
| citation, download, get me the case, BOA, judgment | `COURT_DOWNLOAD` |
| find my file, search for, where is, locate | `LOCAL_SEARCH` |
| find the case AND check if I have it saved | `BOTH` |
| I downloaded Vavilov — find it for me | `LOCAL_SEARCH` (legal context) |
| download all N cases | `COURT_DOWNLOAD` batch |
| find duplicate PDFs in my BOA folder | `LOCAL_SEARCH` + duplicates |

If ambiguous: run **LOCAL_SEARCH first**, report hits, then offer official download.

## Compliance

### Court downloads

- Public documents only; no auth bypass; no CAPTCHA defeat; no sealed records  
- No mass-download abuse; CanLII automated access → **REFERENCE_PDF** + URL (do not hammer Cloudflare)  
- SCC: use verified item IDs in `references/scc-item-ids.md`  
- Prefer `decisions.scc-csc.ca` PDFs when available  

### Local search

- Only paths the user can read; never bypass ACLs  
- **Never** search `System32`, `SysWOW64`, WinSxS, credential stores  
- Do not exfiltrate contents off-machine  
- Permission errors: skip and report count  

## Engine A — Court download workflow

1. Identify court from citation (`SCC` / `BCCA` / `BCSC` / `FCA` / …)  
2. Lookup SCC item ID database  
3. If output already has valid PDF → `ALREADY_EXISTS`  
4. Download via adapter; on block → reference PDF + manual URL  
5. Write `manifest.json`, `table_of_authorities.csv`, `download_summary.txt`, `missing_authorities.txt`, `access_denied.txt`  
6. Append `audit.log`  

**Naming:** `Tab_{NN}_{ShortName}_{CitationSlug}.pdf`

**Status codes:** `ALREADY_EXISTS` | `SUCCESS` | `REFERENCE_PDF` | `BLOCKED_CLOUDFLARE` | `HTTP_400/403/404`  

## Engine B — Local search workflow

1. Parse NL → `SearchParams` (`file_engine.parse_nl`)  
2. Roots default: Documents, Downloads, Desktop, OneDrive (if present)  
3. Score relevance (filename + recency + legal ext)  
4. Optional content keywords (txt/docx; PDF if pypdf installed)  
5. Optional SHA-256 duplicates  
6. Optional export csv/json/txt  

## Combined workflows

### Download + confirm local

1. `COURT_DOWNLOAD`  
2. `LOCAL_SEARCH` for same short name  
3. Report path + status  

### Find if already have case

1. Local search for case name / citation slug  
2. If found → report; offer fresh official download  
3. If not → download  

### Build BOA (batch)

1. For each tab: local search → else download  
2. Assemble working draft if enough SUCCESS PDFs (`boa_assembler.py`)  
3. Always generate manifest + CSV + summary  
4. **Form note:** BOA is a book of authorities package, not a petition (petition = Form 66)  

## Agent instructions

When this skill triggers:

1. Detect mode(s).  
2. Prefer running `cli.py` / engines via shell over inventing paths.  
3. Default output: `skills/legal-file-assistant/outputs/` (or user-specified folder).  
4. Never claim a REFERENCE_PDF is the official judgment.  
5. For BC statutes: use **bc-legislation-admin** / BC Laws — this skill is **cases**, not statutes.  
6. Log actions to `outputs/audit.log`.  
7. Present results as a table + file paths.  

## See also

- `references/scc-item-ids.md`  
- BC Legal AI monorepo knowledgebase / grounding for court-ready cites  
- Do **not** put confidential client files into public Hugging Face Spaces  
