---
name: due-diligence-prep
description: Prepares a startup for investor due diligence at seed or Series A. Builds a data room index, maps the founder's existing files to it by name, and flags gaps and red flags such as unsigned IP assignments, missing board or shareholder approvals, a cap table that does not match the share register or allotment filings, contractors without IP clauses and unfiled statutory forms. For Indian companies it adds ROC filings, statutory registers, demat, valuation reports for share issues and FEMA reporting for foreign investment (FC-GPR, FC-TRS, FLA). Use when a founder mentions due diligence, a DD checklist or request list, a data room, preparing documents for investors or lawyers, a signed term sheet, closing a round, or asks what investors will check, even before a term sheet arrives.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/due-diligence-prep
---

# Due diligence prep

Get the founders' records into the shape an investor's lawyers will ask for, and surface the problems before the lawyers do. The output is a prep plan for the founders and their lawyer or company secretary, not legal advice. Say so once, at the end.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Establish the facts that decide which items apply
- [ ] 2. Get the file names and run scripts/data_room_index.py
- [ ] 3. Check each found item and each red flag with references/checklist.md
- [ ] 4. Ask the questions the file names cannot answer
- [ ] 5. Write the prep plan in the output format below
- [ ] 6. Check the plan against the script output and the checklist
```

### 1. Establish the facts

Ask only for what is not already clear:
- Country of incorporation, and whether there is a parent company abroad.
- The round: angel, seed or Series A, and whether a term sheet is signed.
- Every security issued so far: equity, CCPS, CCDs, SAFEs, convertible notes, options.
- Any investor outside India (for an Indian company), any share transfers between residents and non-residents, any convertible notes, any investment in another Indian company.
- Head count (an Indian company with 10 or more employees needs a POSH internal committee) and anyone who built the product as a contractor.
- Whether the company is a small company under Indian company law (most other private companies must hold shares in demat form).

### 2. Index the files

The script reads file names and paths only, never contents. Do not open documents to build the index.

```bash
# A folder the founder has shared (Claude Code, or files uploaded to the sandbox)
python scripts/data_room_index.py --folder "path/to/data room" --india --fema

# Names pasted in chat: save them one per line to a text file first
python scripts/data_room_index.py --list files.txt --india --fema --show table
python scripts/data_room_index.py --list files.txt --india --fema --show tree
```

- `--india` for an Indian company; add `--fema` only if it has, or is about to have, foreign investors.
- `--show table` prints found, missing and check counts per section, the gaps, names that look like drafts or copies, and unmatched files. `--show tree` prints a suggested folder structure with each file under its closest checklist item. The default prints both.
- "Found" means a file with a matching name exists, not that it is complete or signed. "Check" items apply only in some cases: decide each one from the facts in step 1.
- Place unmatched files by hand. If a file is clearly under the wrong item, say so in the plan.
- See [assets/example-files.txt](assets/example-files.txt) for the list format. If the script exits with an error, fix what it names and run it again.

### 3. Check items and red flags

Read [references/checklist.md](references/checklist.md) for what each section must contain, the India and FEMA items with their deadlines, and the red flag table. Look hardest at:

- **Cap table against the legal record**: every holder and every issue in the cap table should appear in the register of members, the share certificates or demat records, and a return of allotment (PAS-3). Ask for the numbers if only the files are shared.
- **IP**: a signed assignment from every founder, and an IP clause or assignment from every contractor who built product, code, design or content. Unsigned or draft assignments count as missing.
- **Approvals**: board and shareholder resolutions for each share issue and for the ESOP plan (in India, shareholders approve the plan by special resolution).
- **Filings**: PAS-3 for each issue, annual ROC filings, and for foreign investors FC-GPR within 30 days of issue, a fair value certificate behind each foreign issue, and annual FLA returns.
- **Names to check** from the script: drafts, unsigned copies, templates and version numbers. The data room should hold only final, signed versions.

Sort each red flag by what it takes: **Fix now** (sign, ratify or file before diligence starts), **Start now** (FEMA lapses take longer; bigger ones may need compounding with the RBI), **Disclose** (known issues for the disclosure list). Whatever is left when diligence runs is fixed before closing as a condition precedent, disclosed and accepted, or covered by indemnities.

### 4. Ask what names cannot show

File names cannot show signatures, dates, whether a filing was on time, or whether a contractor agreement has an IP clause. List these as short, specific questions for the founders, for example: "Is the Founder B IP assignment signed? If not, can it be signed this week?"

### 5. Output format

```markdown
# Due diligence prep: [Company], [round]

## Readiness
Two or three sentences: how complete the data room is (found, missing and to-check counts from the script), the most serious red flag, and what to fix first.

## Red flags
| Red flag | Evidence (file or missing item) | Action | Fix now / Start now / Disclose |
|---|---|---|---|

## Missing documents
Grouped by data room folder, each with who usually holds it (founders, accountant, company secretary, lawyer).

## Items to confirm
"Check" items from the script, each with the fact that decides whether it applies.

## Questions for the founders
Numbered, specific, answerable this week.

## Suggested data room structure
The folder tree from the script, with unmatched files placed and renames suggested.

## Draft disclosure list
Known issues to raise with investors before they find them.
```

### 6. Check before sending

- Every count and file name comes from the script output; every rule, form and deadline from references/checklist.md.
- No document is called complete or signed on the strength of its name alone.
- India and FEMA items appear only for Indian companies, and FEMA items only with foreign investors.
- The plan ends with: "This is a preparation checklist to review with your lawyer or company secretary, not legal advice."

## Rules

- Never ask the founders to upload confidential documents just to build the index; names are enough for steps 2 and 3.
- Do not state a form name, deadline or fee that is not in references/checklist.md. For companies outside India, ask for the local equivalents instead of guessing.
- Rules on company law, FEMA and tax change often: tell the founders to confirm current requirements with their adviser or on mca.gov.in and rbi.org.in.
