#!/usr/bin/env python3
"""Data room index: map a startup's file names to a due diligence checklist.

Reads file NAMES only, never file contents, so it is safe to point at a
folder of confidential documents. Standard library only, no network, so it
runs in the Claude API sandbox, on claude.ai and in Claude Code.

Usage:
  python scripts/data_room_index.py --folder "path/to/shared drive" [--india] [--fema]
  python scripts/data_room_index.py --list assets/example-files.txt --india --fema
  python scripts/data_room_index.py --list files.txt --india --show table
  python scripts/data_room_index.py --list files.txt --india --show tree

--folder walks a folder and its subfolders. --list reads a text file with one
file name or path per line (blank lines and lines starting with # are skipped),
for when the founder pastes names instead of sharing a folder.
--india adds Indian company-law, tax and employment items; --fema adds the
foreign-investment items for an Indian company with investors outside India.
--show table prints found / missing / check counts and the gaps; --show tree
prints a suggested folder structure with each file under its best match.

Matching is by keywords in the file name and path, so "found" means a file
with a matching name exists, not that the document is complete or signed.
"""
import argparse
import os
import re
import sys

# Pointing --folder at a whole drive by mistake would list far more than any
# data room holds; stop and ask for the right folder instead.
MAX_FILES = 5000
# Operating-system and editor files that are never documents.
JUNK_NAMES = {"thumbs.db", "desktop.ini", ".ds_store"}
JUNK_DIRS = {"__macosx", ".git"}

# Sections in the order StartupReader's startup-due-diligence-checklist
# explainer suggests for data room folders. Scope: core (every company),
# india (Indian companies), fema (Indian companies with foreign investors).
SECTIONS = [
    ("corporate", "Corporate records"),
    ("captable", "Cap table and ESOP"),
    ("finance", "Finance"),
    ("tax", "Tax"),
    ("ip", "Intellectual property"),
    ("contracts", "Contracts"),
    ("people", "People"),
    ("fema", "FEMA (foreign investment)"),
    ("regulatory", "Regulatory, litigation and disclosures"),
]

# (section, scope, label, condition or None, keywords). A keyword is a phrase
# matched as whole words in the normalised path, or a tuple of phrases that
# must all appear. Items with a condition show "check", not "missing", when
# nothing matches, because they apply only to some companies.
ITEMS = [
    ("corporate", "core", "Certificate of incorporation", None,
     ["certificate of incorporation", "incorporation certificate", "incorporation", "coi"]),
    ("corporate", "core", "Memorandum and articles, with amendments", None,
     ["memorandum", "articles", "moa", "aoa", "charter", "bylaws"]),
    ("corporate", "core", "Board minutes and resolutions", None,
     ["board"]),
    ("corporate", "core", "Shareholder minutes and resolutions", None,
     ["shareholder resolution", "shareholders resolution", "members resolution", "special resolution",
      "ordinary resolution", "general meeting", "egm", "agm", "stockholder consent"]),
    ("corporate", "india", "Statutory registers (register of members and others)", None,
     ["register of members", "statutory register", "statutory registers", "register", "registers"]),
    ("corporate", "core", "Founders' agreement", None,
     ["founders agreement", "founder agreement", "cofounder agreement", "co founder agreement"]),
    ("corporate", "core", "Earlier investment agreements (SHA, SSA, SAFE, notes)", None,
     ["sha", "ssa", "shareholders agreement", "shareholder agreement", "subscription agreement",
      "investment agreement", "safe", "convertible note", "ccps", "ccd", "term sheet"]),
    ("corporate", "india", "ROC annual filings: financial statements and annual return", None,
     ["aoc 4", "mgt 7", "mgt 7a", "annual return", "roc"]),
    ("corporate", "india", "Demat records for the company's shares",
     "most private companies other than small companies",
     ["demat", "isin", "nsdl", "cdsl", "depository"]),
    ("captable", "core", "Fully diluted cap table", None,
     ["cap table", "capitalisation table", "capitalization table", "shareholding pattern", "shareholding"]),
    ("captable", "core", "Share certificates", None,
     ["share certificate", "share certificates", "stock certificate", "stock certificates"]),
    ("captable", "india", "Return of allotment for every issue (PAS-3)", None,
     ["pas 3", "return of allotment"]),
    ("captable", "core", "Valuation report for every share issue", None,
     ["valuation report", "valuation", "fair value", "fmv", "409a"]),
    ("captable", "india", "Offer letter for every private placement", None,
     ["pas 4", "pas 5", "private placement"]),
    ("captable", "core", "ESOP plan", None,
     ["esop plan", "esop scheme", "esop policy", "stock option plan", "option plan", "equity incentive plan"]),
    ("captable", "core", "Option grant letters and vesting records", None,
     ["grant letter", "grant letters", "option grant", "esop grant", "option agreement", "vesting"]),
    ("finance", "core", "Audited financial statements", None,
     ["audited", "audit report", "financial statements", "balance sheet", "annual accounts", "financials"]),
    ("finance", "core", "Recent management accounts", None,
     ["management accounts", "mis", "monthly accounts", "management report", "profit and loss", "p l"]),
    ("finance", "core", "Bank statements", None,
     ["bank statement", "bank statements", "bank"]),
    ("tax", "core", "Indirect tax registrations and returns (GST, VAT)", None,
     ["gst", "gstr", "vat", "sales tax"]),
    ("tax", "india", "TDS deposits and TDS returns", None,
     ["tds", "24q", "26q"]),
    ("tax", "core", "Income tax returns, assessments and notices", None,
     ["income tax", "itr", "tax return", "tax returns", "assessment", "tax notice"]),
    ("tax", "india", "Provident fund and ESI registrations and payments",
     "where they apply to the company",
     ["pf", "epf", "epfo", "provident fund", "esi", "esic"]),
    ("ip", "core", "IP assignment from each founder", None,
     [("assignment", "founder"), ("ip", "founder"), ("invention", "founder")]),
    ("ip", "core", "Contractor agreements with IP assignment", None,
     ["contractor", "contractors", "consultant", "consultancy", "freelance", "freelancer", "agency agreement"]),
    ("ip", "core", "Trademarks, domains and other registered IP", None,
     ["trademark", "trade mark", "tm application", "patent", "copyright", "domain", "domains"]),
    ("contracts", "core", "Key customer contracts", None,
     ["customer", "customers", "client", "msa", "master services", "master service", "order form",
      "statement of work", "sow", "pilot agreement"]),
    ("contracts", "core", "Key supplier and partner contracts", None,
     ["supplier", "vendor", "partner", "partnership", "reseller", "distribution", "licence agreement",
      "license agreement"]),
    ("people", "core", "Employment contracts (confidentiality, invention assignment)", None,
     ["employment", "employee agreement", "appointment letter", "offer letter", "offer letters"]),
    ("people", "india", "POSH Act internal committee",
     "if the company has 10 or more employees",
     ["posh", "internal committee", "sexual harassment"]),
    ("people", "core", "Privacy policy and personal data handling", None,
     ["privacy", "data protection", "dpdp", "dpa", "personal data"]),
    ("fema", "fema", "FC-GPR for every issue to a foreign investor", None,
     ["fc gpr", "fcgpr"]),
    ("fema", "fema", "Fair value certificate for every foreign issue", None,
     ["fair value certificate", "fair valuation certificate", ("fema", "valuation"), ("fema", "fair value")]),
    ("fema", "fema", "Annual FLA returns", None,
     ["fla", "foreign liabilities and assets"]),
    ("fema", "fema", "Beneficial ownership check (land-border rules)", None,
     ["beneficial owner", "beneficial ownership", "ubo", "land border", "press note 3"]),
    ("fema", "fema", "FC-TRS, Form CN, Form DI",
     "only for transfers with non-residents, convertible notes or downstream investment",
     ["fc trs", "fctrs", "form cn", "form di", "downstream"]),
    ("regulatory", "core", "Sector licences", "if the business needs any",
     ["licence", "license", "licences", "licenses", "permit"]),
    ("regulatory", "core", "Litigation, disputes and regulatory notices", "if there are any",
     ["litigation", "legal notice", "dispute", "court", "arbitration", "show cause"]),
    ("regulatory", "core", "Disclosure list of known issues", None,
     ["disclosure", "disclosures", "known issues"]),
]

# Names that suggest a file is not the final, signed version. Checked on the
# file name only. The explainer's advice: keep only final, signed versions.
NAME_FLAGS = [
    (r"\bunsigned\b", "unsigned"),
    (r"\bdraft\b", "draft"),
    (r"\btemplate\b", "template, not a signed document"),
    (r"\b(redline|redlined|tracked|markup)\b", "marked-up version"),
    (r"\b(old|backup|wip)\b", "working or old copy"),
    (r"\bv\d+\b|\bversion\s*\d+\b", "version number: confirm it is the final one"),
    (r"\(\d+\)|(?<!certified) copy\s*$", "looks like a duplicate download"),
]


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def normalise(text):
    """Lower-case words: camelCase and letter/digit runs split, punctuation dropped."""
    text = re.sub(r"['’]", "", text)
    text = text.replace("&", " and ")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", text)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def strip_extension(path):
    root, ext = os.path.splitext(path)
    return root if 0 < len(ext) <= 6 else path


def keyword_score(words, keyword):
    """Length of the matched keyword (longer means more specific), or 0."""
    parts = keyword if isinstance(keyword, tuple) else (keyword,)
    score = 0
    for part in parts:
        phrase = normalise(part)
        if f" {phrase} " not in words:
            return 0
        score += len(phrase)
    return score


def read_folder(folder):
    if not os.path.exists(folder):
        fail(f"folder not found: {folder}")
    if not os.path.isdir(folder):
        fail(f"not a folder: {folder} (use --list for a text file of names)")
    unreadable = []
    paths = []
    for root, dirs, files in os.walk(folder, onerror=lambda e: unreadable.append(e.filename)):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d.lower() not in JUNK_DIRS)
        for name in files:
            if name.startswith(".") or name.startswith("~$") or name.lower() in JUNK_NAMES:
                continue
            paths.append(os.path.relpath(os.path.join(root, name), folder).replace(os.sep, "/"))
            if len(paths) > MAX_FILES:
                fail(f"more than {MAX_FILES:,} files under {folder}: point --folder at the data room folder, not a whole drive")
    for name in unreadable:
        print(f"Note: could not open {name}; its files are not counted.")
    return sorted(paths, key=str.lower)


def read_list(list_file):
    if os.path.isdir(list_file):
        fail(f"{list_file} is a folder: use --folder for a folder, --list for a text file of names")
    if not os.path.isfile(list_file):
        fail(f"list file not found: {list_file}")
    try:
        with open(list_file, encoding="utf-8-sig", errors="replace") as handle:
            lines = handle.read().splitlines()
    except OSError as error:
        fail(f"cannot read {list_file}: {error.strerror}")
    seen = set()
    paths = []
    for line in lines:
        name = line.strip().replace("\\", "/").strip("/")
        if not name or name.startswith("#") or name in seen:
            continue
        seen.add(name)
        paths.append(name)
    if len(paths) > MAX_FILES:
        fail(f"more than {MAX_FILES:,} names in {list_file}: list the data room files only")
    return paths


def build(paths, scopes):
    items = [item for item in ITEMS if item[1] in scopes]
    sections = [s for s in SECTIONS if any(item[0] == s[0] for item in items)]
    folder_names = {key: f"{i:02d} {label}" for i, (key, label) in enumerate(sections, 1)}
    matches = {i: [] for i in range(len(items))}
    best = {}
    for path in paths:
        words = f" {normalise(strip_extension(path))} "
        scored = []
        for i, item in enumerate(items):
            score = max(keyword_score(words, k) for k in item[4])
            if score:
                matches[i].append(path)
                scored.append((-score, i))
        if scored:
            best[path] = min(scored)[1]
    return items, sections, folder_names, matches, best


def name_flags(paths):
    flagged = []
    for path in paths:
        name = strip_extension(path.rsplit("/", 1)[-1]).lower().replace("_", " ")
        reasons = [reason for pattern, reason in NAME_FLAGS if re.search(pattern, name)]
        if reasons:
            flagged.append((path, "; ".join(reasons)))
    return flagged


def print_table(items, sections, folder_names, matches):
    status = {}
    for i, item in enumerate(items):
        status[i] = "found" if matches[i] else ("check" if item[3] else "missing")
    print(f"  {'Section':<42}  {'Found':>5}  {'Missing':>7}  {'Check':>5}")
    for key, _ in sections:
        ids = [i for i, item in enumerate(items) if item[0] == key]
        counts = [sum(1 for i in ids if status[i] == s) for s in ("found", "missing", "check")]
        print(f"  {folder_names[key]:<42}  {counts[0]:>5}  {counts[1]:>7}  {counts[2]:>5}")
    missing = [i for i in status if status[i] == "missing"]
    check = [i for i in status if status[i] == "check"]
    if missing:
        print("Missing")
        for i in missing:
            print(f"  {folder_names[items[i][0]][:2]}  {items[i][2]}")
    if check:
        print("Check: needed only in some cases")
        for i in check:
            print(f"  {folder_names[items[i][0]][:2]}  {items[i][2]}: {items[i][3]}")


def print_tree(paths, items, sections, folder_names, best):
    print("Suggested folder structure (each file under its closest match; add an index to each folder)")
    for key, _ in sections:
        files = [p for p in paths if p in best and items[best[p]][0] == key]
        print(f"{folder_names[key]}/" + ("" if files else "  (empty)"))
        for path in files:
            print(f"  {path}  [{items[best[path]][2]}]")
    unsorted = [p for p in paths if p not in best]
    if unsorted:
        print("To sort by hand/")
        for path in unsorted:
            print(f"  {path}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # File names can hold characters the console cannot show: print "?" rather than crash.
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--folder", help="folder to walk (file names only are read)")
    source.add_argument("--list", dest="list_file", help="text file with one file name or path per line")
    parser.add_argument("--india", action="store_true", help="add Indian company-law, tax and employment items")
    parser.add_argument("--fema", action="store_true", help="add foreign-investment (FEMA) items; needs --india")
    parser.add_argument("--show", choices=["all", "table", "tree"], default="all",
                        help="table: found / missing counts and gaps; tree: suggested folders; all: both")
    args = parser.parse_args()
    if args.fema and not args.india:
        fail("--fema covers Indian foreign-investment filings, so it needs --india as well")

    paths = read_folder(args.folder) if args.folder else read_list(args.list_file)
    scopes = {"core"} | ({"india"} if args.india else set()) | ({"fema"} if args.fema else set())
    items, sections, folder_names, matches, best = build(paths, scopes)
    source_name = args.folder or args.list_file
    found = sum(1 for i in matches if matches[i])
    scope_label = " + ".join(["core"] + (["India"] if args.india else []) + (["FEMA"] if args.fema else []))
    noun = "file name" if len(paths) == 1 else "file names"
    print(f"Data room check: {len(paths)} {noun} from {source_name} (names only; no file was opened)")
    print(f"Checklist: {scope_label}, {len(items)} items, {found} with a matching file")
    if not paths:
        print("Note: no files found, so every item shows as missing or to check.")

    if args.show in ("all", "table"):
        print_table(items, sections, folder_names, matches)
        flagged = name_flags(paths)
        if flagged:
            print("Names to check (keep only final, signed versions)")
            for path, reason in flagged:
                print(f"  {path}: {reason}")
        unmatched = [p for p in paths if p not in best]
        if unmatched:
            print("Not matched to any item (place by hand)")
            for path in unmatched:
                print(f"  {path}")
    if args.show in ("all", "tree"):
        print_tree(paths, items, sections, folder_names, best)


if __name__ == "__main__":
    main()
