#!/usr/bin/env python3
"""Founder equity: weighted-factor split, vesting, leavers and dilution.

Standard library only, so it runs in the Claude API sandbox (no network, no
package installs), on claude.ai and in Claude Code.

Usage:
  python scripts/equity_split.py split --founder Riley:10,8,6,9,4,5 --founder Morgan:10,4,8,3,9,5
  python scripts/equity_split.py vesting --shares 5000000 [--credit 6] [--at 18,30] [--cliff 12] [--total 48]
  python scripts/equity_split.py leave --founder Riley:5000000 --founder Morgan:5000000 \
      --leaver Morgan --months 18 [--credit 6] [--others 0]
  python scripts/equity_split.py dilute --founder Riley:5000000 --founder Morgan:5000000 [--pool 0] \
      --round "Pre-seed:500000:2000000" --round "Seed:2000000:8000000:0.10"

split scores each founder 0 to 10 on six factors, in this order: full-time
commitment, idea and early work, domain expertise, building the product,
sales and fundraising, money put in. A round is NAME:RAISE:PRE-MONEY[:POOL],
with POOL the option pool after the round as a fraction of post-money.
Results are a starting point for the founders' conversation, not legal advice.
"""
import argparse
import sys
from decimal import ROUND_HALF_UP, Decimal

# The factors and weights of StartupReader's founder equity split calculator
# (startupreader.com/tools/equity-split-calculator). Keep them in step with it.
FACTORS = [
    ("Full-time commitment", 3),
    ("Idea and early work", 1),
    ("Domain expertise", 2),
    ("Building the product", 2),
    ("Sales and fundraising", 2),
    ("Money put in", 1),
]
MAX_SCORE = 10
MAX_POOL = 0.5  # the site's dilution calculator caps the option pool at 50%


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def money(x):
    return f"{x:,.0f}"


def pct(x):
    """One decimal, halves rounded up like the site's calculators (31.25 -> 31.3)."""
    return f"{Decimal(x * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


def parse_number(text, what, whole=False):
    try:
        value = float(text)
    except ValueError:
        fail(f"{what} must be a number, not \"{text}\"")
    if value != value or value in (float("inf"), float("-inf")):
        fail(f"{what} must be a number, not \"{text}\"")
    if whole and value != int(value):
        fail(f"{what} must be a whole number")
    return value


def founders(specs, parse_value):
    """Parses repeated --founder NAME:VALUE options."""
    if not specs or len(specs) < 2:
        fail("give at least two founders, each as --founder NAME:VALUE")
    out = []
    for spec in specs:
        name, sep, value = spec.rpartition(":")
        name = name.strip()
        if not sep or not name:
            fail(f"--founder \"{spec}\" must look like NAME:VALUE")
        if name in (n for n, _ in out):
            fail(f"founder \"{name}\" is listed twice")
        out.append((name, parse_value(name, value)))
    return out


def vested(shares, months, credit, cliff, total):
    """Shares vested after `months` plus `credit` months: none before the cliff,
    then the same fraction each month until `total` months, rounded down."""
    counted = months + credit
    if counted < cliff:
        return 0
    return int(shares * min(counted, total) // total)


def check_schedule(args):
    if args.total <= 0 or args.total != int(args.total):
        fail("--total must be a whole number of months above 0")
    if not 0 <= args.cliff <= args.total or args.cliff != int(args.cliff):
        fail("--cliff must be a whole number of months between 0 and --total")
    if args.credit < 0 or args.credit != int(args.credit):
        fail("--credit must be a whole number of months, 0 or more")


def split(args):
    def scores(name, text):
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != len(FACTORS):
            fail(f"{name} needs {len(FACTORS)} scores in factor order (commitment, idea, expertise, building, sales, money), got {len(parts)}")
        values = [parse_number(p, f"{name}'s score") for p in parts]
        for (label, _), v in zip(FACTORS, values):
            if not 0 <= v <= MAX_SCORE:
                fail(f"{name}'s score for {label} must be between 0 and {MAX_SCORE}")
        return values

    team = founders(args.founder, scores)
    points = [sum(w * s for (_, w), s in zip(FACTORS, sc)) for _, sc in team]
    total = sum(points)
    shares = [p / total for p in points] if total > 0 else [1 / len(team)] * len(team)
    w = max(len(n) for n, _ in team)
    col = max(w, 6)
    print("Weighted-factor founder split (StartupReader equity split calculator weights)")
    print(f"  {'Factor':<22}  {'Weight':>6}  " + "  ".join(f"{n:>{col}}" for n, _ in team))
    for i, (label, weight) in enumerate(FACTORS):
        print(f"  {label:<22}  {'x' + str(weight):>6}  " + "  ".join(f"{sc[i]:>{col}g}" for _, sc in team))
    print(f"  {'Points':<22}  {'':>6}  " + "  ".join(f"{p:>{col}g}" for p in points) + f"  (of {total:g})")
    print(f"  {'Suggested split':<22}  {'':>6}  " + "  ".join(f"{pct(s):>{col}}" for s in shares))
    if total == 0:
        print("Every score is 0, so the split is equal.")


def vesting(args):
    check_schedule(args)
    if args.shares <= 0 or args.shares != int(args.shares):
        fail("--shares must be a whole number above 0")
    extra = [int(parse_number(m, "--at", whole=True)) for m in args.at.split(",") if m.strip()] if args.at else []
    if any(m < 0 for m in extra):
        fail("--at months must be 0 or more")
    shares, credit, cliff, total = int(args.shares), int(args.credit), int(args.cliff), int(args.total)
    # Rows: signing, the month before the cliff, the cliff, each anniversary after it, full vesting.
    counted = [cliff - 1, cliff] + list(range(cliff + 12, total, 12)) + [total]
    months = sorted({0, *(c - credit for c in counted if c - credit >= 0), *extra})
    print(f"Founder vesting: {money(shares)} shares over {total} months, {cliff}-month cliff, then monthly")
    if credit:
        when = f"the cliff is reached {cliff - credit} months after signing" if cliff > credit else "the cliff has passed by signing"
        print(f"Credit for time already worked: {credit} months, so {when}"
              f" and everything has vested {max(0, total - credit)} months after signing")
    print(f"  {'Months after signing':>20}  {'Months counted':>14}  {'Vested shares':>13}  {'Vested':>7}  {'Unvested shares':>15}")
    for m in months:
        v = vested(shares, m, credit, cliff, total)
        print(f"  {m:>20}  {m + credit:>14}  {money(v):>13}  {pct(v / shares):>7}  {money(shares - v):>15}")


def leave(args):
    check_schedule(args)

    def whole(name, text):
        v = parse_number(text, f"{name}'s shares", whole=True)
        if v <= 0:
            fail(f"{name}'s shares must be above 0")
        return int(v)

    team = founders(args.founder, whole)
    names = [n for n, _ in team]
    if args.leaver not in names:
        fail(f"--leaver must be one of {', '.join(names)}")
    if args.months < 0 or args.months != int(args.months):
        fail("--months must be a whole number of months, 0 or more")
    if args.others < 0 or args.others != int(args.others):
        fail("--others must be a whole number of shares, 0 or more")
    months, credit = int(args.months), int(args.credit)
    held = dict(team)
    kept = vested(held[args.leaver], months, credit, int(args.cliff), int(args.total))
    after = {n: (kept if n == args.leaver else s) for n, s in team}
    rows = [(n, held[n], after[n]) for n in names]
    if args.others:
        rows.append(("Everyone else", int(args.others), int(args.others)))
    before_total = sum(b for _, b, _ in rows)
    after_total = sum(a for _, _, a in rows)
    print(f"{args.leaver} leaves {months} months after signing ({months + credit} months counted;"
          f" {int(args.cliff)}-month cliff, fully vested at {int(args.total)})")
    print(f"  {args.leaver} keeps {money(kept)} of {money(held[args.leaver])} shares ({pct(kept / held[args.leaver])} vested);"
          f" {money(held[args.leaver] - kept)} unvested shares go back to the company")
    w = max(len("Holder"), len("Everyone else") if args.others else 0, *(len(n) for n in names))
    print(f"  {'Holder':<{w}}  {'Shares before':>13}  {'%':>6}  {'Shares after':>13}  {'%':>6}")
    for n, b, a in rows:
        print(f"  {n:<{w}}  {money(b):>13}  {pct(b / before_total):>6}  {money(a):>13}  {pct(a / after_total):>6}")
    print(f"  {'Total':<{w}}  {money(before_total):>13}  {pct(1):>6}  {money(after_total):>13}  {pct(1):>6}")


def dilute(args):
    def whole(name, text):
        v = parse_number(text, f"{name}'s shares", whole=True)
        if v <= 0:
            fail(f"{name}'s shares must be above 0")
        return int(v)

    team = founders(args.founder, whole)
    if not args.round:
        fail("give at least one --round NAME:RAISE:PRE-MONEY[:POOL]")
    if args.pool < 0:
        fail("--pool must be 0 or more shares")
    if args.pool / (sum(s for _, s in team) + args.pool) > MAX_POOL:
        fail(f"--pool must be at most {pct(MAX_POOL)} of the company at founding")
    rounds = []
    for spec in args.round:
        parts = spec.split(":")
        if len(parts) not in (3, 4) or not parts[0].strip():
            fail(f"--round \"{spec}\" must look like NAME:RAISE:PRE-MONEY or NAME:RAISE:PRE-MONEY:POOL")
        name = parts[0].strip()
        raise_ = parse_number(parts[1], f"{name}'s raise")
        pre = parse_number(parts[2], f"{name}'s pre-money")
        pool = parse_number(parts[3], f"{name}'s pool target") if len(parts) == 4 else 0.0
        if raise_ <= 0 or pre <= 0:
            fail(f"{name}'s raise and pre-money must both be above 0")
        if not 0 <= pool <= MAX_POOL:
            fail(f"{name}'s pool target must be a fraction between 0 and {MAX_POOL} (0.10 for 10%)")
        if f"{name} investors" in [n for n, _ in team] or name in [r[0] for r in rounds]:
            fail(f"round name \"{name}\" is used twice or clashes with a founder")
        rounds.append((name, raise_, pre, pool))

    def simulate(with_pool):
        """The site's dilution calculator: new money scales everyone, then the
        pool is topped up to its target out of everyone except the pool."""
        founder_total = sum(s for _, s in team) + args.pool
        stakes = {n: s / founder_total for n, s in team}
        pool = args.pool / founder_total
        stages = [("Founding", 0.0, dict(stakes), pool)]
        for name, raise_, pre, target in rounds:
            post = pre + raise_
            new = raise_ / post
            stakes = {n: v * (1 - new) for n, v in stakes.items()}
            pool *= 1 - new
            target = target if with_pool else 0.0
            if target > pool:
                others = sum(stakes.values())
                deficit = min(target - pool, others)
                keep = (others - deficit) / others if others > 0 else 1
                stakes = {n: v * keep for n, v in stakes.items()}
                pool += deficit
            stakes[f"{name} investors"] = new
            stages.append((name, post, dict(stakes), pool))
        return stages

    stages = simulate(True)
    names = [n for n, _ in team]
    holders = names + [f"{r[0]} investors" for r in rounds]
    w = max(len("Option pool"), len("Post-money"), *(len(h) for h in holders), *(len(f"{n} paper value") for n in names))
    col = max(10, *(len(s[0]) for s in stages), *(len(money(s[1])) for s in stages))
    print("Dilution by round (pool top-ups come out of everyone but the new investors)")
    print(f"  {'Holder':<{w}}  " + "  ".join(f"{s[0]:>{col}}" for s in stages))
    for h in holders[: len(names)]:
        print(f"  {h:<{w}}  " + "  ".join(f"{pct(s[2][h]):>{col}}" for s in stages))
    print(f"  {'Option pool':<{w}}  " + "  ".join(f"{(pct(s[3]) if s[3] else '-'):>{col}}" for s in stages))
    for h in holders[len(names):]:
        print(f"  {h:<{w}}  " + "  ".join(f"{(pct(s[2][h]) if h in s[2] else '-'):>{col}}" for s in stages))
    print(f"  {'Post-money':<{w}}  " + "  ".join(f"{(money(s[1]) if s[1] else '-'):>{col}}" for s in stages))
    for n in names:
        print(f"  {n + ' paper value':<{w}}  " + "  ".join(f"{(money(s[2][n] * s[1]) if s[1] else '-'):>{col}}" for s in stages))
    last = stages[-1][2]
    combined = sum(last[n] for n in names)
    print("Founders' split of their combined shares after the last round: "
          + ", ".join(f"{n} {pct(last[n] / combined)}" for n in names) + " (unchanged by rounds and pool top-ups)")
    if any(r[3] for r in rounds):
        no_pool = simulate(False)[-1][2]
        print("Without the pool top-ups, after the last round: "
              + ", ".join(f"{n} {pct(no_pool[n])} ({(no_pool[n] - last[n]) * 100:.1f} points more)" for n in names))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("split", help="weighted-factor split from 0-10 scores")
    s.add_argument("--founder", action="append", help="NAME:commitment,idea,expertise,building,sales,money (repeat per founder)")
    s.set_defaults(run=split)

    def schedule(p):
        p.add_argument("--credit", type=float, default=0, help="months already worked that count toward vesting")
        p.add_argument("--cliff", type=float, default=12, help="cliff in months (default 12)")
        p.add_argument("--total", type=float, default=48, help="vesting period in months (default 48)")

    v = sub.add_parser("vesting", help="vesting schedule for one founder's shares")
    v.add_argument("--shares", type=float, required=True)
    v.add_argument("--at", help="extra months after signing to show, comma-separated, e.g. 18,30")
    schedule(v)
    v.set_defaults(run=vesting)

    lv = sub.add_parser("leave", help="what a leaving founder keeps and the split afterwards")
    lv.add_argument("--founder", action="append", help="NAME:SHARES (repeat per founder)")
    lv.add_argument("--leaver", required=True)
    lv.add_argument("--months", type=float, required=True, help="months after signing when the founder leaves")
    lv.add_argument("--others", type=float, default=0, help="shares held by everyone else (investors, pool)")
    schedule(lv)
    lv.set_defaults(run=leave)

    d = sub.add_parser("dilute", help="founders' stakes after funding rounds and pool top-ups")
    d.add_argument("--founder", action="append", help="NAME:SHARES (repeat per founder)")
    d.add_argument("--pool", type=float, default=0, help="option pool shares that exist at founding")
    d.add_argument("--round", action="append", help="NAME:RAISE:PRE-MONEY[:POOL], in order (repeat per round)")
    d.set_defaults(run=dilute)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
