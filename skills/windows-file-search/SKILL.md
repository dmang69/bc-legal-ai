---
name: windows-file-search
description: >
  Windows desktop file and folder search assistant. Searches local Windows file
  systems for files and folders by name, extension, date, size, or content.
  Returns full paths, metadata, and relevance ranking. ALWAYS trigger when user
  says: 'find my file', 'search for', 'where is my', 'locate the PDF of',
  'find all my court documents', 'search my downloads for', 'find the latest',
  'show me files modified last week', 'find folders containing', 'search inside
  my documents', 'find duplicates', or any request to locate files or folders
  on a local Windows machine. Also trigger for: 'organize my files', 'find
  everything related to my court case', 'export file list to CSV'.
  Aliases: file-search, folder-search, windows-search, file-finder.
---

# Windows Desktop File and Folder Search

Searches local Windows file systems quickly and safely. Natural language queries,
filters, content search, duplicate detection, and CSV/JSON/TXT export.

**Not for remote systems** unless the user names those roots. Never exfiltrate contents off-machine.

## Scripts

```text
skills/windows-file-search/
  SKILL.md
  scripts/file_engine.py
  scripts/cli.py
  outputs/
```

```powershell
cd C:\Users\Dizzle\projects\bc-legal-ai\skills\windows-file-search\scripts

python cli.py --query "vavilov" --ext .pdf
python cli.py --query "modified last week" --export csv
python cli.py --query "duplicates" --duplicates --root "$env:USERPROFILE\Downloads"
python cli.py --query "court documents" --json
python cli.py --query "search inside documents for tenancy" --ext .pdf
```

## Operating rules

| Do | Don't |
|----|--------|
| Search only user-readable paths | Bypass ACLs / security |
| Skip protected system areas | Touch System32, SysWOW64, WinSxS, credential stores |
| Report permission skips | Dump full file contents into logs |
| Prefer user home defaults | Search entire C:\ unless asked |

**Never touch:** `System32`, `SysWOW64`, SAM/SECURITY/SYSTEM hives, credential vaults.  
`Program Files` excluded by default unless user adds root.

## Default roots

Documents, Downloads, Desktop, OneDrive (if present), plus monorepo legal skill `outputs` when present.

## Engines (priority)

1. **PowerShell `Get-ChildItem`** — fast name/filter on Windows  
2. **Python `os.walk`** — full filters, content, folders, date/size  
3. Windows Search Index COM — optional (not required; often restricted)

## NL parsing examples

| User says | Effect |
|-----------|--------|
| find the latest contract PDF | `.pdf`, query≈contract, sort date |
| where is the Vavilov PDF | query=vavilov, `.pdf` |
| find anything modified last week | date_from = −7d |
| find duplicates in Downloads | root=Downloads, `find_duplicates` |
| search inside my documents for 990A | content_keywords |
| find all my court documents | legal-ish exts + court terms |

## Relevance

Exact name 1.0 · partial 0.7 · folder 0.6 · content 0.5 · recent +0.1–0.2 · home +0.1 · PDF/DOCX +0.05

## Agent workflow

1. Parse request with `parse_nl` / `cli.py`.  
2. Run search; never invent paths.  
3. Present table: score, type, path, size, modified.  
4. If zero hits: suggest broader terms / other roots.  
5. Export to `outputs/search_results.{csv,json,txt}` when asked.  
6. For **downloading** cases, hand off to **canadian-court-downloader**.  
7. For **combined** download+find, use **legal-file-assistant**.  

## Content search formats

| Format | Method |
|--------|--------|
| txt/md/csv/json/html | Direct read |
| PDF | pypdf text extract (scanned → note OCR) |
| DOCX | zip + document.xml |

## Safety checklist

- `os.access(..., R_OK)` before read  
- `try/except PermissionError` everywhere  
- Report `permission_skipped` / `protected_skipped` counts  
- No registry / no remote SMB unless user gives path  
