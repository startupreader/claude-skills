#!/usr/bin/env python3
"""Startup India eligibility checks: DPIIT recognition, the Section 80-IAC tax
holiday, ESOP tax deferral, the Seed Fund Scheme and the Credit Guarantee
Scheme, from a company's facts.

Prints only the tests that depend on dates and thresholds (age limits, the
turnover limit in any financial year, the 80-IAC incorporation window, the
years a tax holiday could cover). Judgement calls such as innovation are
echoed as stated. Standard library only, no network access.

Usage:
  python scripts/eligibility.py assets/example-company.json
  python scripts/eligibility.py assets/example-company.json --only 80iac \
      --turnover 2029-30=1040000000
  python scripts/eligibility.py --entity private-limited --incorporated 2024-06-03 \
      --turnover 2024-25="18 lakh" --turnover 2025-26="1.2 crore" \
      [--name "Example Pvt Ltd"] [--as-of 2026-11-08] [--deep-tech no] \
      [--split no] [--used-plant no] [--innovation yes] [--recognised yes] \
      [--imb-certificate no] [--indian-promoters 100] [--govt-support 0] \
      [--foreign-investors no] [--in-default no] [--profit 2027-28=5000000]
      [--only dpiit|80iac|seed-fund|cgss|dates]

A JSON file uses the same facts with underscores (see assets/example-company.json);
arguments override the file. Yes/no facts take yes, no or unknown. Amounts are
rupees: 12500000, "1.25 crore" or "12.5 lakh". Financial years run from April to
March and are written 2025-26. Dates are YYYY-MM-DD.

Thresholds were last checked on 2026-11-08 (references/rules.md). Indian rules
change in Budgets, so confirm them on the official portals. Not tax or legal advice.
"""
import argparse
import json
import re
import sys
from datetime import date

LAKH = 100_000
CRORE = 10_000_000

# DPIIT startup definition, startupindia.gov.in recognition page (G.S.R. 108(E)).
DPIIT_MAX_AGE_YEARS = 10  # "considered a startup for up to 10 years ... from the date of its incorporation"
DPIIT_DEEPTECH_MAX_AGE_YEARS = 20  # "(20 years for DeepTech startups)"
DPIIT_TURNOVER_LIMIT = 200 * CRORE  # "less than INR 200 Crores ... in any of the previous financial years"
DPIIT_DEEPTECH_TURNOVER_LIMIT = 300 * CRORE  # "(INR 300 Crores for DeepTech startups)"

# Section 80-IAC of the Income-tax Act, 1961, now Section 140 of the Income-tax Act, 2025.
IAC_INCORPORATED_FROM = date(2016, 4, 1)  # Section 140(16)(b)(i): "on or after the 1st April, 2016"
IAC_INCORPORATED_BEFORE = date(2030, 4, 1)  # Section 140(16)(b)(i): "but before the 1st April, 2030"
IAC_MAX_AGE_YEARS = 10  # Startup India 80-IAC page: "Must be less than 10 years old"
IAC_TURNOVER_LIMIT = 100 * CRORE  # Startup India: "less than ₹100 crore in any financial year"; Act: "does not exceed" in the year claimed
IAC_WINDOW_YEARS = 10  # Section 140(2): "out of ten years beginning from the year in which the eligible start-up is incorporated"
IAC_HOLIDAY_YEARS = 3  # Section 140(2): "any three consecutive tax years"
IAC_GROWTH_1Y = 0.10  # Startup India declaration of scalability: "More than 10% growth in revenue from one financial year to the next"
IAC_GROWTH_2Y = 0.25  # "More than 25% cumulative growth in revenue over a period of two financial years"
IAC_GROWTH_3Y = 0.33  # "More than 33% cumulative growth in revenue over a period of three financial years"
IAC_USED_PLANT_SHARE = 0.20  # Section 140(6): used plant or machinery up to 20% of the total value is allowed

# Startup India Seed Fund Scheme, seedfund.startupindia.gov.in/about.
SEED_MAX_AGE_YEARS = 2  # "incorporated not more than 2 years ago at the time of application"
SEED_MIN_INDIAN_PROMOTERS_PCT = 51  # "Shareholding by Indian promoters ... at least 51%"
SEED_MAX_OTHER_SUPPORT = 10 * LAKH  # "should not have received more than Rs 10 lakh of monetary support"

OK, NO, CHECK = "Eligible", "Not eligible", "Needs checking"
RANK = {OK: 0, CHECK: 1, NO: 2}

# Entity type: (label, on the DPIIT list, can claim 80-IAC). None means "needs checking".
ENTITY_TYPES = {
    "private-limited": ("private limited company", True, True),
    "llp": ("limited liability partnership", True, True),
    "registered-partnership": ("registered partnership firm", True, False),
    "cooperative-society": ("cooperative society", True, False),
    "one-person-company": ("one person company", None, None),
    "public-limited": ("public limited company", False, False),
    "unregistered-partnership": ("unregistered partnership firm", False, False),
    "sole-proprietorship": ("sole proprietorship", False, False),
}
ALIASES = {
    "pvt-ltd": "private-limited",
    "private-limited-company": "private-limited",
    "limited-liability-partnership": "llp",
    "registered-partnership-firm": "registered-partnership",
    "co-operative-society": "cooperative-society",
    "opc": "one-person-company",
    "proprietorship": "sole-proprietorship",
}
BOOL_FACTS = ["deep_tech", "split_or_reconstructed", "reused_plant_or_machinery", "innovation",
              "dpiit_recognised", "imb_certificate", "foreign_investors", "in_default"]
KNOWN_FACTS = set(BOOL_FACTS) | {"name", "entity_type", "incorporated", "as_of", "turnover", "profit",
                                 "indian_promoters_pct", "other_government_support", "note"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def inr(amount):
    """Rupees in crore and lakh: ₹11.5 crore, ₹6.4 lakh, ₹45,000."""
    sign = "-" if amount < 0 else ""
    a = abs(amount)
    trim = lambda x: f"{x:.2f}".rstrip("0").rstrip(".")
    if a >= CRORE:
        return f"{sign}₹{trim(a / CRORE)} crore"
    if a >= LAKH:
        return f"{sign}₹{trim(a / LAKH)} lakh"
    return f"{sign}₹{round(a):,}"


def fmt(d):
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def parse_date(value, what):
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        fail(f"{what} must be a date written YYYY-MM-DD, got {value!r}")


def parse_bool(value, what):
    if value is None or isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("yes", "y", "true"):
        return True
    if s in ("no", "n", "false"):
        return False
    if s in ("unknown", "not stated", ""):
        return None
    fail(f"{what} must be yes, no or unknown, got {value!r}")


def parse_amount(value, what):
    if isinstance(value, bool):
        fail(f"{what} must be an amount in rupees, got {value!r}")
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"^(₹|rs\.?|inr)\s*", "", str(value).strip().lower()).replace(",", "")
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?)?", s)
    if not m:
        fail(f"{what} must be rupees, e.g. 12500000, \"1.25 crore\" or \"12.5 lakh\", got {value!r}")
    unit = m.group(2) or ""
    return float(m.group(1)) * (CRORE if unit.startswith("cr") else LAKH if unit.startswith("la") else 1)


def parse_fy(label):
    """'2025-26', 'FY 2025-26' or '2025-2026' -> 2025 (the year the FY starts in April)."""
    s = re.sub(r"^fy\s*", "", str(label).strip().lower())
    m = re.fullmatch(r"(\d{4})\s*[-/]\s*(\d{2}|\d{4})", s)
    if not m:
        fail(f"financial year must be written like 2025-26, got {label!r}")
    start, end = int(m.group(1)), m.group(2)
    if (len(end) == 2 and int(end) != (start + 1) % 100) or (len(end) == 4 and int(end) != start + 1):
        fail(f"financial year {label!r} must span two consecutive years, e.g. 2025-26")
    return start


def fy_of(d):
    """Indian financial years run 1 April to 31 March."""
    return d.year if d.month >= 4 else d.year - 1


def fy(start):
    return f"FY {start}-{(start + 1) % 100:02d}"


def add_years(d, n):
    try:
        return d.replace(year=d.year + n)
    except ValueError:  # 29 February: use 28 February
        return d.replace(year=d.year + n, day=28)


def age_text(start, end):
    months = (end.year - start.year) * 12 + end.month - start.month - (1 if end.day < start.day else 0)
    plural = lambda n, unit: f"{n} {unit}" + ("" if n == 1 else "s")
    parts = [plural(months // 12, "year")] if months >= 12 else []
    return " ".join(parts + [plural(months % 12, "month")])


def worst(statuses):
    return max(statuses, key=lambda s: RANK[s]) if statuses else OK


def line(status, text):
    return f"  {status:<15} {text}"


def by_year(raw, what, inc_fy, allow_negative):
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        fail(f"{what} must map financial years to rupees, e.g. {{\"2025-26\": 12500000}}")
    out = {}
    for label, value in raw.items():
        start = parse_fy(label)
        if start < inc_fy:
            fail(f"{what} is given for {fy(start)}, before the company was incorporated ({fy(inc_fy)})")
        amount = parse_amount(value, f"{what} for {fy(start)}")
        if amount < 0 and not allow_negative:
            fail(f"{what} for {fy(start)} cannot be negative")
        out[start] = amount
    return out


def load_facts(args):
    facts = {}
    if args.facts:
        try:
            with open(args.facts, encoding="utf-8") as fh:
                facts = json.load(fh)
        except OSError as e:
            fail(f"cannot read {args.facts}: {e.strerror}")
        except json.JSONDecodeError as e:
            fail(f"{args.facts} is not valid JSON: {e}")
        if not isinstance(facts, dict):
            fail(f"{args.facts} must hold one JSON object of facts")
        unknown = sorted(set(facts) - KNOWN_FACTS)
        if unknown:
            fail(f"unknown fact(s) in {args.facts}: {', '.join(unknown)}. Known: {', '.join(sorted(KNOWN_FACTS))}")
    overrides = {
        "name": args.name, "entity_type": args.entity, "incorporated": args.incorporated, "as_of": args.as_of,
        "deep_tech": args.deep_tech, "split_or_reconstructed": args.split, "reused_plant_or_machinery": args.used_plant,
        "innovation": args.innovation, "dpiit_recognised": args.recognised, "imb_certificate": args.imb_certificate,
        "indian_promoters_pct": args.indian_promoters, "other_government_support": args.govt_support,
        "foreign_investors": args.foreign_investors, "in_default": args.in_default,
    }
    facts.update({k: v for k, v in overrides.items() if v is not None})
    for key, pairs in (("turnover", args.turnover), ("profit", args.profit)):
        for pair in pairs or []:
            if "=" not in pair:
                fail(f"--{key} takes FY=AMOUNT, e.g. 2025-26=12500000, got {pair!r}")
            label, value = pair.split("=", 1)
            facts[key] = dict(facts.get(key) or {}, **{label.strip(): value.strip()})

    if not facts.get("entity_type"):
        fail("the entity type is required (--entity or entity_type), e.g. private-limited")
    if not facts.get("incorporated"):
        fail("the incorporation date is required (--incorporated or incorporated), e.g. 2021-08-12")
    entity = re.sub(r"[\s_]+", "-", str(facts["entity_type"]).strip().lower())
    entity = ALIASES.get(entity, entity)
    if entity not in ENTITY_TYPES:
        fail(f"unknown entity type {facts['entity_type']!r}. Use one of: {', '.join(ENTITY_TYPES)}")
    f = {"name": facts.get("name") or "the company", "entity": entity}
    f["incorporated"] = parse_date(facts["incorporated"], "incorporated")
    f["as_of"] = parse_date(facts["as_of"], "as_of") if facts.get("as_of") else date.today()
    if f["incorporated"] > f["as_of"]:
        fail(f"incorporated ({f['incorporated']}) is after the as-of date ({f['as_of']})")
    for key in BOOL_FACTS:
        f[key] = parse_bool(facts.get(key), key)
    f["promoters"] = None
    if facts.get("indian_promoters_pct") is not None:
        f["promoters"] = parse_amount(facts["indian_promoters_pct"], "indian_promoters_pct")
        if not 0 <= f["promoters"] <= 100:
            fail("indian_promoters_pct is a percentage between 0 and 100, e.g. 82")
    f["support"] = None
    if facts.get("other_government_support") is not None:
        f["support"] = parse_amount(facts["other_government_support"], "other_government_support")
    inc_fy = fy_of(f["incorporated"])
    f["turnover"] = by_year(facts.get("turnover"), "turnover", inc_fy, allow_negative=False)
    f["profit"] = by_year(facts.get("profit"), "profit", inc_fy, allow_negative=True)
    return f


def check_dpiit(f):
    inc, asof, deep = f["incorporated"], f["as_of"], f["deep_tech"]
    label, on_list, _ = ENTITY_TYPES[f["entity"]]
    rows = []
    if on_list:
        rows.append((OK, f"Entity type: {label} is on the list"))
    elif on_list is None:
        rows.append((CHECK, f"Entity type: {label}; the list names private limited companies, so confirm on NSWS"))
    else:
        rows.append((NO, f"Entity type: {label} is not on the list (private limited, registered partnership, LLP, cooperative)"))

    limit, deep_limit = add_years(inc, DPIIT_MAX_AGE_YEARS), add_years(inc, DPIIT_DEEPTECH_MAX_AGE_YEARS)
    age = age_text(inc, asof)
    if asof < limit:
        rows.append((OK, f"Age {age}: the {DPIIT_MAX_AGE_YEARS}-year limit is reached on {fmt(limit)}"))
    elif deep and asof < deep_limit:
        rows.append((CHECK, f"Age {age}: passes only as DeepTech ({DPIIT_DEEPTECH_MAX_AGE_YEARS}-year limit, {fmt(deep_limit)}), which DPIIT decides"))
    else:
        years = DPIIT_DEEPTECH_MAX_AGE_YEARS if deep else DPIIT_MAX_AGE_YEARS
        rows.append((NO, f"Age {age}: the {years}-year limit passed on {fmt(deep_limit if deep else limit)}"))

    current = fy_of(asof)
    given = {y: t for y, t in f["turnover"].items() if y <= current}
    if not given:
        rows.append((CHECK, f"Turnover: none given; the {inr(DPIIT_TURNOVER_LIMIT)} limit applies to every FY since incorporation"))
    else:
        peak_fy = max(given, key=lambda y: (given[y], y))
        peak = given[peak_fy]
        where = f"peak {inr(peak)} ({fy(peak_fy)})"
        if peak < DPIIT_TURNOVER_LIMIT:
            rows.append((OK, f"Turnover: {where}; the limit is {inr(DPIIT_TURNOVER_LIMIT)} in any FY"))
        elif peak == DPIIT_TURNOVER_LIMIT:
            rows.append((CHECK, f"Turnover: {where}, exactly at the limit; sources say 'less than' and 'not exceed'"))
        elif deep and peak < DPIIT_DEEPTECH_TURNOVER_LIMIT:
            rows.append((CHECK, f"Turnover: {where}; passes only as DeepTech ({inr(DPIIT_DEEPTECH_TURNOVER_LIMIT)} limit)"))
        elif deep and peak == DPIIT_DEEPTECH_TURNOVER_LIMIT:
            rows.append((CHECK, f"Turnover: {where}, exactly at the DeepTech limit; sources say 'less than' and 'not exceed'"))
        else:
            rows.append((NO, f"Turnover: {where} is over the {inr(DPIIT_DEEPTECH_TURNOVER_LIMIT if deep else DPIIT_TURNOVER_LIMIT)} limit"))
        missing = [fy(y) for y in range(fy_of(inc), current) if y not in given]
        if missing:
            which = ", ".join(missing) if len(missing) <= 3 else f"{len(missing)} FYs from {missing[0]} to {missing[-1]}"
            rows.append((CHECK, f"No turnover given for {which}: the limit applies to every FY"))

    split = f["split_or_reconstructed"]
    rows.append({False: (OK, "Not formed by splitting up or reconstructing a business (as stated)"),
                 True: (NO, "Formed by splitting up or reconstructing an existing business"),
                 None: (CHECK, "Formed by splitting up or reconstructing a business? Not stated")}[split])
    rows.append({True: (OK, "Works on innovation or a scalable model (as stated; DPIIT judges it)"),
                 False: (NO, "Does not work on innovation, improvement or a scalable model (as stated)"),
                 None: (CHECK, "Innovation or scalability: not stated; DPIIT judges it")}[f["innovation"]])
    return worst([s for s, _ in rows]), rows


def recognition_row(f, dpiit_verdict):
    """The benefits below all need recognition, not just eligibility for it."""
    if dpiit_verdict == NO:
        return (NO, "Fails the DPIIT recognition tests above")
    if f["dpiit_recognised"] is not True:
        return (CHECK, "DPIIT recognition not held yet (or not stated): it comes first")
    return None


def growth_row(f):
    complete = sorted(y for y in f["turnover"] if y < fy_of(f["as_of"]))
    if len(complete) < 2:
        return (CHECK, "Revenue growth: needs turnover for two or more completed FYs")
    t = f["turnover"]
    last = complete[-1]
    tests = []
    for years, need in ((1, IAC_GROWTH_1Y), (2, IAC_GROWTH_2Y), (3, IAC_GROWTH_3Y)):
        base = t.get(last - years)
        if base:
            tests.append((years, need, t[last] / base - 1))
    if not tests:
        return (CHECK, f"Revenue growth: no earlier non-zero turnover to compare with {fy(last)}")
    for years, need, growth in tests:
        if growth > need:
            span = "the year before" if years == 1 else f"{years} years before"
            return (OK, f"Revenue growth {fy(last)}: {growth:+.1%} on {span} (needs over {need:.0%})")
    if any(abs(g - n) < 1e-9 for _, n, g in tests):
        return (CHECK, "Revenue growth exactly at a threshold: the declaration says 'more than'")
    years, need, growth = tests[0]
    return (CHECK, f"Revenue growth {fy(last)}: {growth:+.1%}, under every scalability test (over 10%, 25% or 33%)")


def check_80iac(f, dpiit_verdict):
    inc, asof = f["incorporated"], f["as_of"]
    label, _, can_claim = ENTITY_TYPES[f["entity"]]
    rows = []
    if can_claim:
        rows.append((OK, f"Company or LLP: {label}"))
    elif can_claim is None:
        rows.append((CHECK, f"{label.capitalize()}: the criteria name private limited companies and LLPs"))
    else:
        rows.append((NO, f"Only private limited companies and LLPs can claim it, not a {label}"))
    in_window = IAC_INCORPORATED_FROM <= inc < IAC_INCORPORATED_BEFORE
    rows.append((OK if in_window else NO,
                 f"Incorporated {fmt(inc)}: needs {fmt(IAC_INCORPORATED_FROM)} to {fmt(date(2030, 3, 31))}"))
    ten = add_years(inc, IAC_MAX_AGE_YEARS)
    rows.append((OK, f"Under {IAC_MAX_AGE_YEARS} years old until {fmt(ten)}") if asof < ten
                else (NO, f"{IAC_MAX_AGE_YEARS} years old on {fmt(ten)}: too old to apply"))
    current = fy_of(asof)
    given = {y: t for y, t in f["turnover"].items() if y <= current}
    if given:
        peak_fy = max(given, key=lambda y: (given[y], y))
        peak = given[peak_fy]
        if peak < IAC_TURNOVER_LIMIT:
            rows.append((OK, f"Turnover under {inr(IAC_TURNOVER_LIMIT)} in every FY to date (peak {inr(peak)})"))
        elif peak == IAC_TURNOVER_LIMIT:
            rows.append((CHECK, f"Turnover exactly {inr(peak)} in {fy(peak_fy)}: Startup India says 'less than'"))
        else:
            rows.append((NO, f"Turnover {inr(peak)} in {fy(peak_fy)}: Startup India needs under {inr(IAC_TURNOVER_LIMIT)} in every FY"))
    split, plant = f["split_or_reconstructed"], f["reused_plant_or_machinery"]
    if split is True:
        rows.append((NO, "Formed by splitting up or reconstructing an existing business"))
    elif plant is True:
        rows.append((CHECK, f"Uses plant or machinery used before: allowed up to {IAC_USED_PLANT_SHARE:.0%} of the total value"))
    elif split is False and plant is False:
        rows.append((OK, "No splitting up, reconstruction or used plant and machinery (as stated)"))
    else:
        rows.append((CHECK, "Splitting up, reconstruction or used plant and machinery: not stated"))
    rows.append(growth_row(f))
    rec = recognition_row(f, dpiit_verdict)
    if rec:
        rows.append(rec)
    rows.append((OK, "IMB certificate held") if f["imb_certificate"]
                else (CHECK, "IMB certificate not held yet: apply on the Startup India portal"))
    return worst([s for s, _ in rows]), rows, in_window


def holiday_blocks(f):
    """Ten FYs from the FY of incorporation; any three consecutive ones."""
    first, current = fy_of(f["incorporated"]), fy_of(f["as_of"])
    last = first + IAC_WINDOW_YEARS - 1
    starts = list(range(first, last - IAC_HOLIDAY_YEARS + 2))
    past = [s for s in starts if s < current]
    future = [s for s in starts if s >= current]
    out = [f"  Ten-year window {fy(first)} to {fy(last)} (ends {fmt(date(last + 1, 3, 31))})."]
    if future:
        out = [f"  Ten-year window {fy(first)} to {fy(last)}. Three-year blocks (profit as given; losses count as zero):"]
        sums = {}
        for s in future:
            years = range(s, s + IAC_HOLIDAY_YEARS)
            over = [y for y in years if f["turnover"].get(y, 0) > IAC_TURNOVER_LIMIT]
            gaps = [y for y in years if y not in f["profit"]]
            sums[s] = sum(max(0.0, f["profit"].get(y, 0.0)) for y in years if y not in over)
            notes = []
            if over:
                notes.append(f"{', '.join(fy(y) for y in over)} left out: turnover over {inr(IAC_TURNOVER_LIMIT)}")
            if gaps and len(gaps) < IAC_HOLIDAY_YEARS:
                notes.append(f"no profit given for {', '.join(fy(y) for y in gaps)}")
            text = inr(sums[s]) if len(gaps) < IAC_HOLIDAY_YEARS else "no profit given"
            out.append((s, f"    {fy(s)} to {fy(s + 2)}   {text}" + (f"  ({'; '.join(notes)})" if notes else "")))
        best = max(sums, key=lambda s: (sums[s], -s)) if any(sums.values()) else None
        out = [o if isinstance(o, str) else o[1] + ("  <- largest" if o[0] == best else "") for o in out]
    if past:
        span = fy(past[0]) if len(past) == 1 else f"{fy(past[0])} to {fy(past[-1])}"
        out.append(f"  Blocks starting {span} began in past years: ask a CA if any can still be claimed.")
    return out


def check_seed(f, dpiit_verdict):
    rows = []
    rec = recognition_row(f, dpiit_verdict)
    if rec:
        rows.append(rec)
    deadline = add_years(f["incorporated"], SEED_MAX_AGE_YEARS)
    rows.append((OK, f"Within {SEED_MAX_AGE_YEARS} years of incorporation: apply by {fmt(deadline)}") if f["as_of"] <= deadline
                else (NO, f"Must apply within {SEED_MAX_AGE_YEARS} years of incorporation: that passed on {fmt(deadline)}"))
    p = f["promoters"]
    if p is None:
        rows.append((CHECK, f"Indian promoters' shareholding not stated (needs at least {SEED_MIN_INDIAN_PROMOTERS_PCT}%)"))
    else:
        rows.append((OK if p >= SEED_MIN_INDIAN_PROMOTERS_PCT else NO,
                     f"Indian promoters hold {p:g}% (needs at least {SEED_MIN_INDIAN_PROMOTERS_PCT}%)"))
    s = f["support"]
    if s is None:
        rows.append((CHECK, f"Other government monetary support not stated (limit {inr(SEED_MAX_OTHER_SUPPORT)})"))
    else:
        rows.append((OK if s <= SEED_MAX_OTHER_SUPPORT else NO,
                     f"Other government monetary support {inr(s)} (limit {inr(SEED_MAX_OTHER_SUPPORT)})"))
    return worst([st for st, _ in rows]), rows


def check_cgss(f, dpiit_verdict):
    rows = []
    rec = recognition_row(f, dpiit_verdict)
    if rec:
        rows.append(rec)
    rows.append({False: (OK, "Not in default or an NPA (as stated)"),
                 True: (NO, "In default or classed as an NPA"),
                 None: (CHECK, "Default or NPA status not stated")}[f["in_default"]])
    rows.append((CHECK, "Stable revenue over 12 months and the loan itself: the lender assesses them"))
    return worst([s for s, _ in rows]), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("facts", nargs="?", help="JSON file of facts, e.g. assets/example-company.json")
    parser.add_argument("--name")
    parser.add_argument("--entity", help=", ".join(ENTITY_TYPES))
    parser.add_argument("--incorporated", help="YYYY-MM-DD")
    parser.add_argument("--as-of", dest="as_of", help="date to check on, YYYY-MM-DD (default today)")
    parser.add_argument("--turnover", action="append", metavar="FY=AMOUNT", help="repeat per FY, e.g. 2025-26=115000000")
    parser.add_argument("--profit", action="append", metavar="FY=AMOUNT", help="eligible-business profit, actual or projected")
    for flag, dest in (("--deep-tech", "deep_tech"), ("--split", "split"), ("--used-plant", "used_plant"),
                       ("--innovation", "innovation"), ("--recognised", "recognised"),
                       ("--imb-certificate", "imb_certificate"), ("--foreign-investors", "foreign_investors"),
                       ("--in-default", "in_default")):
        parser.add_argument(flag, dest=dest, metavar="yes|no|unknown")
    parser.add_argument("--indian-promoters", dest="indian_promoters", metavar="PCT", help="Indian promoters' shareholding, %%")
    parser.add_argument("--govt-support", dest="govt_support", metavar="AMOUNT", help="money from other government schemes")
    parser.add_argument("--only", choices=["dpiit", "80iac", "seed-fund", "cgss", "dates"])
    args = parser.parse_args()
    f = load_facts(args)
    show = lambda part: args.only in (None, part)

    inc, asof = f["incorporated"], f["as_of"]
    label = ENTITY_TYPES[f["entity"]][0]
    out = [f"Startup India eligibility: {f['name']}",
           f"As of {fmt(asof)} ({fy(fy_of(asof))}). {label[0].upper() + label[1:]}, incorporated {fmt(inc)}."]
    dpiit_verdict, rows = check_dpiit(f)
    if show("dpiit"):
        held = {True: "yes", False: "no", None: "not stated"}[f["dpiit_recognised"]]
        out += ["", f"DPIIT recognition: {dpiit_verdict} (recognition held: {held})"] + [line(*r) for r in rows]
    iac_verdict, rows, in_window = check_80iac(f, dpiit_verdict)
    in_window = in_window and iac_verdict != NO  # no holiday window to plan once a test fails
    if show("80iac"):
        out += ["", f"Section 80-IAC tax holiday (Section 140, Income-tax Act, 2025): {iac_verdict}"]
        out += [line(*r) for r in rows] + (holiday_blocks(f) if in_window else [])
        esop = NO if iac_verdict == NO else OK if f["imb_certificate"] and iac_verdict == OK else CHECK
        out.append(f"ESOP tax deferral for employees: {esop} (only at a start-up with the IMB certificate)")
    if show("seed-fund"):
        verdict, rows = check_seed(f, dpiit_verdict)
        out += ["", f"Startup India Seed Fund Scheme: {verdict}"] + [line(*r) for r in rows]
    if show("cgss"):
        verdict, rows = check_cgss(f, dpiit_verdict)
        out += ["", f"Credit Guarantee Scheme for Startups: {verdict}"] + [line(*r) for r in rows]
    if show("dates"):
        seed = add_years(inc, SEED_MAX_AGE_YEARS)
        dates = [(add_years(inc, DPIIT_MAX_AGE_YEARS), f"DPIIT age limit ({DPIIT_MAX_AGE_YEARS} years from incorporation)"),
                 (seed, "Last day to apply to the Seed Fund Scheme" + (" (passed)" if asof > seed else ""))]
        if f["deep_tech"]:
            dates.append((add_years(inc, DPIIT_DEEPTECH_MAX_AGE_YEARS), f"DeepTech age limit ({DPIIT_DEEPTECH_MAX_AGE_YEARS} years)"))
        if in_window:
            last = fy_of(inc) + IAC_WINDOW_YEARS - 1
            dates.append((date(last + 1, 3, 31), f"End of the 80-IAC ten-year window ({fy(last)})"))
        out += ["", "Key dates"] + [f"  {fmt(d):<12}  {text}" for d, text in sorted(dates)]
        if f["foreign_investors"]:
            out.append(f"Foreign investors: yes. Seed Fund needs Indian promoters at {SEED_MIN_INDIAN_PROMOTERS_PCT}%+;"
                       " FEMA pricing and FC-GPR apply.")
    print("\n".join(out))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass
    main()
