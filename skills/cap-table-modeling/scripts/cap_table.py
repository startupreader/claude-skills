#!/usr/bin/env python3
"""Cap table model: convert SAFEs and notes, top up the option pool, issue a priced round.

Standard library only, so it runs in the Claude API sandbox (no network, no
package installs), on claude.ai and in Claude Code.

Usage:
  python scripts/cap_table.py assets/example-cap-table.json
  python scripts/cap_table.py cap-table.json --pre-money 12000000 --raise 3000000 --pool-target 0.12
  python scripts/cap_table.py cap-table.json --conversions-outside-pre-money

The JSON file (field by field in references/conversion-rules.md):
  holders           [{"name": "Asha (founder)", "shares": 4500000}, ...]
                    everyone with issued shares or granted options today
  unallocated_pool  shares reserved for future grants and not yet granted
  instruments       [{"name", "type", "amount", "cap", "discount", "mfn", ...}]
                    type: post-money-safe, pre-money-safe or note; notes also
                    take "interest_rate" and "years" or "issued" (YYYY-MM-DD)
  round             {"name", "pre_money", "raise", "pool_target", "closing"}

Fractions are decimals: 0.2 for a 20% discount, 0.10 for a 10% pool.
Amounts are in one currency unit; shares are counts. A simplified model for
checking the lawyers' closing cap table, not legal advice.
"""
import argparse
import datetime
import json
import math
import sys
from decimal import ROUND_HALF_UP, Decimal

DAYS_PER_YEAR = 365  # simple interest accrues by actual days over a 365-day year
TOLERANCE = 1e-14  # relative change in share counts at which the conversion maths has settled
MAX_STEPS = 200000  # iterations allowed before deciding the inputs cannot add up
ROUNDING_GUARD = 1e-3  # shares: keeps floating-point noise (999,999.9999) from losing a whole share

# type: (label, cap divides into a count that includes conversion shares, that includes the pool top-up)
TYPES = {
    "post-money-safe": ("post-money SAFE", True, False),
    "pre-money-safe": ("pre-money SAFE", False, True),
    "note": ("convertible note", False, True),
}

TOP_KEYS = {"company", "currency", "holders", "unallocated_pool", "instruments", "round"}
HOLDER_KEYS = {"name", "shares", "founder"}
INSTRUMENT_KEYS = {
    "name", "type", "amount", "cap", "discount", "mfn", "interest_rate", "years", "issued", "maturity",
    "cap_includes_conversions", "cap_includes_pool_top_up",
}
ROUND_KEYS = {"name", "pre_money", "raise", "pool_target", "closing", "investor_name", "conversions_in_pre_money"}


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def money(x):
    return f"{x:,.0f}"


def pct(x, places=2):
    """Halves rounded up like the site's calculators (31.125 -> 31.13)."""
    return f"{Decimal(x * 100).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)}%"


def check_keys(obj, allowed, where):
    if not isinstance(obj, dict):
        fail(f"{where} must be a JSON object")
    unknown = sorted(set(obj) - allowed)
    if unknown:
        fail(f"{where} has unknown field(s): {', '.join(unknown)}. Allowed: {', '.join(sorted(allowed))}")


def number(obj, key, where, default=None, positive=False, below=None):
    value = obj.get(key, default)
    if value is None:
        if default is None:
            fail(f"{where} needs \"{key}\"")
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f"{where}: \"{key}\" must be a number, not {json.dumps(value)}")
    if value < 0 or (positive and value == 0):
        fail(f"{where}: \"{key}\" must be {'above' if positive else 'at least'} 0")
    if below is not None and value >= below:
        fail(f"{where}: \"{key}\" must be below {below:g} (write fractions as decimals, e.g. 0.2 for 20%)")
    return float(value)


def flag(obj, key, where, default):
    value = obj.get(key, default)
    if not isinstance(value, bool):
        fail(f"{where}: \"{key}\" must be true or false")
    return value


def date(obj, key, where):
    value = obj.get(key)
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        fail(f"{where}: \"{key}\" must be a date written YYYY-MM-DD, not {json.dumps(value)}")


def load(path, args):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        fail(f"{path} not found")
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e.msg} at line {e.lineno}")
    check_keys(data, TOP_KEYS, "the file")

    holders = data.get("holders")
    if not isinstance(holders, list) or not holders:
        fail("\"holders\" must be a non-empty list of {\"name\", \"shares\"}")
    names = set()

    def new_name(obj, where):
        name = obj.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"{where} needs a \"name\"")
        if name in names:
            fail(f"the name \"{name}\" is used twice; every holder, instrument and investor needs its own")
        names.add(name)
        return name

    rows = []
    for i, h in enumerate(holders, 1):
        check_keys(h, HOLDER_KEYS, f"holder {i}")
        name = new_name(h, f"holder {i}")
        rows.append((name, number(h, "shares", f"holder \"{name}\"", positive=True), flag(h, "founder", f"holder \"{name}\"", False)))
    pool = number(data, "unallocated_pool", "the file", default=0.0)

    rnd = data.get("round")
    check_keys(rnd, ROUND_KEYS, "\"round\"")
    r = {
        "name": rnd.get("name", "Priced round"),
        "pre": args.pre_money if args.pre_money is not None else number(rnd, "pre_money", "\"round\"", positive=True),
        "raise": args.raise_ if args.raise_ is not None else number(rnd, "raise", "\"round\"", positive=True),
        "pool_target": args.pool_target if args.pool_target is not None else number(rnd, "pool_target", "\"round\"", default=0.0, below=1),
        "closing": date(rnd, "closing", "\"round\""),
        "in_pre": False if args.conversions_outside_pre_money else flag(rnd, "conversions_in_pre_money", "\"round\"", True),
    }
    if not isinstance(r["name"], str) or not r["name"].strip():
        fail("\"round\": \"name\" must be text")
    if r["pre"] <= 0 or r["raise"] <= 0:
        fail("the round's pre-money and raise must both be above 0")
    if not 0 <= r["pool_target"] < 1:
        fail("the pool target must be a fraction between 0 and 1, e.g. 0.10 for 10%")
    investor_share = r["raise"] / (r["pre"] + r["raise"])
    if r["pool_target"] >= 1 - investor_share:
        fail(f"a {pct(r['pool_target'], 1)} pool target leaves nothing for existing holders: the new investors already take {pct(investor_share, 1)}")
    r["investors"] = rnd.get("investor_name", f"{r['name']} investors")
    if not isinstance(r["investors"], str):
        fail("\"round\": \"investor_name\" must be text")
    new_name({"name": r["investors"]}, "\"round\"")
    new_name({"name": "Unallocated pool"}, "the pool")

    instruments = []
    for i, x in enumerate(data.get("instruments") or [], 1):
        check_keys(x, INSTRUMENT_KEYS, f"instrument {i}")
        name = new_name(x, f"instrument {i}")
        where = f"instrument \"{name}\""
        kind = x.get("type")
        if kind not in TYPES:
            fail(f"{where}: \"type\" must be one of {', '.join(TYPES)}")
        label, with_conversions, with_pool = TYPES[kind]
        inst = {
            "order": i,
            "name": name,
            "type": kind,
            "label": label,
            "amount": number(x, "amount", where, positive=True),
            "cap": number(x, "cap", where, default=0.0),
            "discount": number(x, "discount", where, default=0.0, below=1),
            "mfn": flag(x, "mfn", where, False),
            "issued": date(x, "issued", where),
            "maturity": date(x, "maturity", where),
            "with_conversions": flag(x, "cap_includes_conversions", where, with_conversions),
            "with_pool": flag(x, "cap_includes_pool_top_up", where, with_pool),
            "interest": 0.0,
            "years": 0.0,
        }
        rate = number(x, "interest_rate", where, default=0.0, below=1)
        if kind != "note" and (rate or "years" in x):
            fail(f"{where}: only notes carry interest; a SAFE has no interest rate")
        if rate:
            if "years" in x:
                years = number(x, "years", where)
            elif inst["issued"] and r["closing"]:
                years = (r["closing"] - inst["issued"]).days / DAYS_PER_YEAR
                if years < 0:
                    fail(f"{where} is dated after the round's closing date")
            else:
                fail(f"{where}: to add interest, give \"years\", or \"issued\" here and \"closing\" in the round")
            inst["years"] = years
            inst["interest"] = inst["amount"] * rate * years
        inst["rate"] = rate
        inst["converting"] = inst["amount"] + inst["interest"]
        instruments.append(inst)
    return data, rows, pool, instruments, r


def solve(existing, pool, instruments, r):
    """Fixed point of the round: the price depends on the conversion and pool
    shares, and they depend on the price. Every quantity rises with the others,
    so iterating from zero settles on the answer or keeps growing if the
    conversions, pool and new money claim 100% or more of the company."""
    top_up = 0.0
    conv = [0.0] * len(instruments)
    for _ in range(MAX_STEPS):
        converted = sum(conv)
        price = r["pre"] / (existing + top_up + (converted if r["in_pre"] else 0.0))
        new_conv, detail = [], []
        for inst in instruments:
            base = existing + (top_up if inst["with_pool"] else 0.0) + (converted if inst["with_conversions"] else 0.0)
            cap_price = inst["cap"] / base if inst["cap"] else None
            disc_price = price * (1 - inst["discount"]) if inst["discount"] else None
            used = min(p for p in (cap_price, disc_price, price) if p is not None)
            how = "cap" if used == cap_price else ("round price" if used == price else "discount")
            new_conv.append(inst["converting"] / used)
            detail.append((cap_price, disc_price, used, how))
        total = existing + top_up + sum(new_conv) + r["raise"] / price
        new_top_up = max(0.0, r["pool_target"] * total - pool)
        change = max([abs(a - b) for a, b in zip(new_conv, conv)] + [abs(new_top_up - top_up)])
        conv, top_up = new_conv, new_top_up
        if change <= TOLERANCE * total:
            return price, top_up, conv, detail
        if total > existing * 1e9:
            break
    fail("the SAFEs, notes, pool target and new money add up to 100% or more of the company; check the caps, amounts and pool target")


def later(a, b):
    """True if instrument b was issued after a: by date when both have one, else by order in the file."""
    if a["issued"] and b["issued"]:
        return b["issued"] > a["issued"]
    return b["order"] > a["order"]


def run(args):
    data, rows, pool, instruments, r = load(args.file, args)
    existing = sum(s for _, s, _ in rows) + pool
    price, top_up, conv, detail = solve(existing, pool, instruments, r)

    top_up_shares = math.floor(top_up + 0.5)
    conv_shares = [math.floor(c + ROUNDING_GUARD) for c in conv]
    investor_shares = math.floor(r["raise"] / price + ROUNDING_GUARD)
    total_after = existing + top_up_shares + sum(conv_shares) + investor_shares
    company = data.get("company", "Company")
    currency = f" (amounts in {data['currency']})" if data.get("currency") else ""

    print(f"Cap table model: {company}, {r['name']}{currency}")
    print(f"Round: {money(r['raise'])} new money at a {money(r['pre'])} pre-money ({money(r['pre'] + r['raise'])} post-money)")
    if r["pool_target"]:
        print(f"Unallocated pool target after the round: {pct(r['pool_target'], 1)} of the fully diluted company")
    else:
        print("No option pool target: the pool is not topped up")
    if not r["in_pre"]:
        print("SAFE and note conversions sit outside the pre-money, so they dilute the new investors too")

    if instruments:
        w = max(len("Instrument"), *(len(i["name"]) for i in instruments))
        print()
        print("Conversions (each converts at the lowest of its cap price, discount price and the round price)")
        print(f"  {'Instrument':<{w}}  {'Type':<16}  {'Converting':>11}  {'Cap price':>9}  {'Disc. price':>11}  {'Converts at':<11}  {'Shares':>11}")
        for inst, (cap_price, disc_price, used, how), shares in zip(instruments, detail, conv_shares):
            cap_s = f"{cap_price:.4f}" if cap_price is not None else "-"
            disc_s = f"{disc_price:.4f}" if disc_price is not None else "-"
            print(f"  {inst['name']:<{w}}  {inst['label']:<16}  {money(inst['converting']):>11}  {cap_s:>9}  {disc_s:>11}  {how:<11}  {money(shares):>11}")
        for inst in instruments:
            if inst["interest"]:
                print(f"  {inst['name']}: {money(inst['amount'])} principal + {money(inst['interest'])} simple interest"
                      f" ({pct(inst['rate'], 1)} a year for {inst['years']:.2f} years)")

    pre_count = existing + top_up + (sum(conv) if r["in_pre"] else 0.0)
    print()
    print(f"Round price per share: {price:.4f}  ({money(r['pre'])} pre-money / {money(pre_count)} pre-money fully diluted shares)")

    w = max(len("Holder"), len("Unallocated pool"), len(r["investors"]), *(len(n) for n, _, _ in rows), *(len(i["name"]) for i in instruments))
    print()
    print(f"  {'Holder':<{w}}  {'Shares before':>13}  {'% before':>8}  {'Shares after':>13}  {'% after':>8}")
    table = [(n, s, s) for n, s, _ in rows]
    if pool or top_up_shares:
        table.append(("Unallocated pool", pool, pool + top_up_shares))
    table += [(i["name"], None, s) for i, s in zip(instruments, conv_shares)]
    table.append((r["investors"], None, investor_shares))
    for name, before, after in table:
        b = f"{money(before):>13}  {pct(before / existing):>8}" if before is not None else f"{'-':>13}  {'-':>8}"
        print(f"  {name:<{w}}  {b}  {money(after):>13}  {pct(after / total_after):>8}")
    print(f"  {'Total':<{w}}  {money(existing):>13}  {pct(1):>8}  {money(total_after):>13}  {pct(1):>8}")
    founder_shares = sum(s for _, s, is_founder in rows if is_founder)
    if founder_shares:
        print(f"Founders together: {money(founder_shares)} shares, {pct(founder_shares / existing)} before, {pct(founder_shares / total_after)} after")
    if instruments:
        print(f"SAFEs and notes together: {money(sum(conv_shares))} shares, {pct(sum(conv_shares) / total_after)} after")

    effective = round(price * existing)
    pool_value = round(price * top_up)
    print()
    print(f"Effective pre-money for today's holders: {money(effective)}  (headline {money(r['pre'])})")
    conv_value = r["pre"] - effective - pool_value if r["in_pre"] else 0
    if not r["in_pre"]:
        pool_value = r["pre"] - effective
    parts = [f"today's holders {money(effective)}"]
    if pool_value:
        parts.append(f"pool top-up {money(pool_value)}")
    if conv_value:
        parts.append(f"SAFE and note conversions {money(conv_value)}")
    if len(parts) > 1:
        print(f"  Headline {money(r['pre'])} = {' + '.join(parts)}")
    print(f"Post-money at the round price: {money(price * (existing + top_up + sum(conv)) + r['raise'])}")

    notes = []
    if r["pool_target"] and top_up == 0:
        notes.append(f"The unallocated pool is already at or above {pct(r['pool_target'], 1)} of the company after the round, so nothing is added.")
    for inst in instruments:
        if inst["maturity"] and r["closing"] and r["closing"] > inst["maturity"]:
            notes.append(f"{inst['name']} reached maturity on {inst['maturity'].isoformat()}, before the closing: check what the note says happens at maturity.")
        if not inst["mfn"]:
            continue
        better = []
        for other in instruments:
            if other is inst or not later(inst, other):
                continue
            terms = []
            if other["cap"] and (not inst["cap"] or other["cap"] < inst["cap"]):
                terms.append(f"cap {money(other['cap'])}, {other['label']}")
            if other["discount"] > inst["discount"]:
                terms.append(f"discount {pct(other['discount'], 0)}")
            if terms:
                better.append(f"{other['name']} ({'; '.join(terms)})")
        if better:
            notes.append(f"{inst['name']} has an MFN clause, and later instruments have better terms: {', '.join(better)}."
                         " If the clause lets the holder adopt them, re-run with those terms.")
        else:
            notes.append(f"{inst['name']} has an MFN clause; no later instrument in the file has better terms.")
    if notes:
        print()
        print("Notes")
        for n in notes:
            print(f"  - {n}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="cap table JSON file")
    parser.add_argument("--pre-money", type=float, help="override the round's pre-money valuation")
    parser.add_argument("--raise", dest="raise_", metavar="RAISE", type=float, help="override the new money raised")
    parser.add_argument("--pool-target", type=float, help="override the unallocated pool target, a fraction of post-money")
    parser.add_argument("--conversions-outside-pre-money", action="store_true",
                        help="price the round on today's shares and the pool only, so conversions dilute the new investors too")
    args = parser.parse_args()
    for value, label in ((args.pre_money, "--pre-money"), (args.raise_, "--raise")):
        if value is not None and not (math.isfinite(value) and value > 0):
            fail(f"{label} must be a number above 0")
    if args.pool_target is not None and not (math.isfinite(args.pool_target) and 0 <= args.pool_target < 1):
        fail("--pool-target must be a fraction between 0 and 1, e.g. 0.10 for 10%")
    run(args)


if __name__ == "__main__":
    main()
