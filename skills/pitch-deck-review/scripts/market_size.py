#!/usr/bin/env python3
"""Pitch deck arithmetic: bottom-up market size, runway and use of funds, growth.

Standard library only, so it runs in the Claude API sandbox (no network, no
package installs), on claude.ai and in Claude Code.

Usage:
  python scripts/market_size.py market \
      --segment "Independent clinics" 40000 1200 50% \
      --segment "Group practices" 6000 4800 25% \
      --som-share 3% [--monthly] [--claimed-tam 4200000000] \
      [--claimed-sam N] [--claimed-som N] [--revenue-target 2400000]
  python scripts/market_size.py runway --raise 1500000 --burn 60000:6,85000 \
      [--cash 100000] [--claimed-months 24] [--pre-money 6000000] \
      [--use "Product and engineering" 45% --use "Sales and marketing" 35% ...]
  python scripts/market_size.py growth --start 8000 --end 30000 --periods 9 \
      [--per month|quarter|year] [--claimed-rate 40%]

market: each --segment is NAME CUSTOMERS PRICE [SERVICEABLE]. PRICE is revenue
per customer per year (per month with --monthly). SERVICEABLE is the share of
those customers the product and sales channels can reach today (default 100%).
TAM = customers x price over all segments; SAM = the serviceable part;
SOM = --som-share of SAM, the part the company can win in the plan period.

runway: --burn is planned monthly net burn (spending minus revenue) after the
round, as AMOUNT or phases AMOUNT:MONTHS,...,AMOUNT. The last phase has no
month count: it runs until the cash is gone. --use values are all amounts or
all percentages of the raise.

Shares and rates take a fraction (0.03) or a percentage (3%); write a negative
rate as --claimed-rate=-5%. Amounts are in one currency unit and may use commas. The results check a deck's arithmetic;
they are not a forecast.
"""
import argparse
import math
import sys

MONTHS_PER_YEAR = 12
PERIODS_PER_YEAR = {"month": 12, "quarter": 4, "year": 1}
# StartupReader's startup-funding-stages explainer: rounds are usually sized to
# last 18 to 24 months, and the next round should be prepared with about a
# year of runway left, because a raise itself takes three to six months.
USUAL_RUNWAY_MONTHS = (18, 24)
NEXT_RAISE_LEAD_MONTHS = 12
# Same explainer: each priced round commonly sells 10% to 25% of the company.
USUAL_ROUND_STAKE = (0.10, 0.25)
# Use-of-funds lines within half a percentage point of the raise count as adding up
# (decks round each line to a whole percentage).
ROUNDING_TOLERANCE = 0.005


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def money(x):
    return f"{x:,.0f}"


def pct(x):
    return f"{x * 100:.1f}%"


def number(text, what):
    try:
        value = float(str(text).replace(",", "").replace("_", "").strip())
    except ValueError:
        fail(f"{what} must be a number, got {text!r}")
    if not math.isfinite(value):
        fail(f"{what} must be a finite number, got {text!r}")
    return value


def share(text, what):
    """A fraction (0.03) or a percentage (3%). Without a % sign, values above 1
    are ambiguous (is 5 meant as 5% or 500%?), so they are refused."""
    raw = str(text).strip()
    if raw.endswith("%"):
        return number(raw[:-1], what) / 100
    value = number(raw, what)
    if value > 1:
        fail(f"{what} must be a fraction like 0.05 or a percentage like 5%, got {text!r}")
    return value


def periods_text(n, unit):
    return f"{n:g} {unit}" + ("" if n == 1 else "s")


def optional_positive(value, flag):
    if value is None:
        return None
    result = number(value, flag)
    if result <= 0:
        fail(f"{flag} must be positive")
    return result


def market(args):
    if not args.segment:
        fail("give at least one --segment NAME CUSTOMERS PRICE [SERVICEABLE]")
    rows = []
    for seg in args.segment:
        if len(seg) not in (3, 4):
            fail(f"--segment needs NAME CUSTOMERS PRICE [SERVICEABLE], got {len(seg)} values: {' '.join(seg)}")
        name = seg[0].strip()
        if not name:
            fail("--segment NAME is empty")
        count = number(seg[1], f"customers for {name!r}")
        price = number(seg[2], f"price for {name!r}")
        reach = share(seg[3], f"serviceable share for {name!r}") if len(seg) == 4 else 1.0
        if count <= 0 or price <= 0:
            fail(f"customers and price for {name!r} must be positive")
        if not 0 < reach <= 1:
            fail(f"serviceable share for {name!r} must be above 0 and at most 100%")
        if args.monthly:
            price *= MONTHS_PER_YEAR
        rows.append((name, count, price, reach))
    som_share = None
    if args.som_share is not None:
        som_share = share(args.som_share, "--som-share")
        if not 0 < som_share <= 1:
            fail("--som-share must be above 0 and at most 100%")
    claimed_tam = optional_positive(args.claimed_tam, "--claimed-tam")
    claimed_sam = optional_positive(args.claimed_sam, "--claimed-sam")
    claimed_som = optional_positive(args.claimed_som, "--claimed-som")
    target = optional_positive(args.revenue_target, "--revenue-target")

    tam = sum(c * p for _, c, p, _ in rows)
    sam = sum(c * p * r for _, c, p, r in rows)
    customers = sum(c for _, c, _, _ in rows)
    reachable = sum(c * r for _, c, _, r in rows)
    width = max(len("Segment"), *(len(n) for n, _, _, _ in rows))

    print("Bottom-up market size (annual revenue; price per customer per year)")
    print(f"  {'Segment':<{width}}  {'Customers':>11}  {'Price/yr':>9}  {'TAM':>14}  {'Reach':>6}  {'SAM':>14}")
    for name, count, price, reach in rows:
        print(f"  {name:<{width}}  {money(count):>11}  {money(price):>9}  {money(count * price):>14}"
              f"  {reach * 100:>5.0f}%  {money(count * price * reach):>14}")
    summary = [("TAM", "every customer in every segment", tam, customers),
               ("SAM", "the part the product can reach", sam, reachable)]
    if som_share is not None:
        summary.append(("SOM", f"{pct(som_share)} of SAM", sam * som_share, reachable * som_share))
    for label, what, value, count in summary:
        print(f"  {label}  {what:<32}  {money(value):>14}  ({money(count)} customers)")
    if claimed_tam:
        print(f"  Deck's TAM {money(claimed_tam)} is {claimed_tam / tam:,.1f}x the bottom-up TAM.")
    if claimed_sam:
        print(f"  Deck's SAM {money(claimed_sam)} is {claimed_sam / sam:,.1f}x the bottom-up SAM.")
    if claimed_som:
        print(f"  Deck's SOM {money(claimed_som)} is {pct(claimed_som / sam)} of the bottom-up SAM.")
    if target:
        line = f"  Revenue target {money(target)}: {pct(target / sam)} of SAM"
        if som_share is not None:
            line += f", {target / (sam * som_share):,.2f}x the SOM"
        print(line + ".")
        avg_price = sam / reachable
        print(f"  At the average serviceable price ({money(avg_price)}) that is {money(target / avg_price)} customers.")


def parse_burn(text):
    phases = []
    parts = [p.strip() for p in str(text).split(",") if p.strip()]
    if not parts:
        fail("--burn is empty: give a monthly amount, e.g. 60000, or phases, e.g. 60000:6,85000")
    for i, part in enumerate(parts):
        amount_text, _, months_text = part.partition(":")
        amount = number(amount_text, "--burn amount")
        if i == len(parts) - 1:
            if months_text:
                fail("--burn: leave the month count off the last phase (it runs until the cash is gone), e.g. 60000:6,85000")
            phases.append((amount, None))
            continue
        if not months_text:
            fail(f"--burn: phase {part!r} needs a month count, e.g. 60000:6 (commas separate phases, so write 60000 not 60,000)")
        months = number(months_text, "--burn months")
        if months <= 0:
            fail(f"--burn: months in {part!r} must be positive")
        phases.append((amount, months))
    return phases


def where(value, low, high):
    return "below" if value < low else ("above" if value > high else "within")


def runway(args):
    raise_ = number(args.raise_, "--raise")
    cash = number(args.cash, "--cash")
    if raise_ <= 0:
        fail("--raise must be positive")
    if cash < 0:
        fail("--cash must be zero or more")
    phases = parse_burn(args.burn)
    claimed = optional_positive(args.claimed_months, "--claimed-months")
    pre_money = optional_positive(args.pre_money, "--pre-money")
    uses = []
    if args.use:
        percent_mode = [value.strip().endswith("%") for _, value in args.use]
        if any(percent_mode) and not all(percent_mode):
            fail("--use values must be all amounts or all percentages, not a mix")
        for name, value in args.use:
            if all(percent_mode):
                amount = share(value, f"--use {name!r}") * raise_
            else:
                amount = number(value, f"--use {name!r}")
            if amount < 0:
                fail(f"--use {name!r} must not be negative")
            uses.append((name, amount))

    total_cash = raise_ + cash
    print(f"Runway: raise {money(raise_)} + cash in the bank {money(cash)} = {money(total_cash)}")
    elapsed = 0.0
    remaining = total_cash
    months = None
    for amount, length in phases:
        span = f"months {elapsed:g} to {elapsed + length:g}" if length else f"from month {elapsed:g}"
        print(f"  Net burn {money(amount)} a month, {span}")
        if amount > 0 and (length is None or amount * length >= remaining):
            months = elapsed + remaining / amount
            break
        if length is None:
            break
        remaining -= amount * length
        elapsed += length
    if months is None:
        print(f"  Cash does not run out on this plan: net burn is zero or below from month {elapsed:g}.")
    else:
        low, high = USUAL_RUNWAY_MONTHS
        print(f"  Runway: {months:.1f} months")
        print(f"  Rounds are usually sized to last {low} to {high} months; this is {where(months, low, high)} that range.")
        if months > NEXT_RAISE_LEAD_MONTHS:
            print(f"  Start preparing the next round by month {months - NEXT_RAISE_LEAD_MONTHS:.1f}"
                  f" ({NEXT_RAISE_LEAD_MONTHS} months of runway left).")
        else:
            print(f"  Runway is {NEXT_RAISE_LEAD_MONTHS} months or less from the start: the next raise starts now.")
    if claimed:
        if months is None:
            print(f"  Deck claims {claimed:g} months; on this plan the cash does not run out.")
        else:
            gap = months - claimed
            if abs(gap) < 0.05:
                verdict = "matches that"
            elif gap < 0:
                verdict = f"is {-gap:.1f} months short of that"
            else:
                verdict = f"gives {gap:.1f} months more than that"
            print(f"  Deck claims {claimed:g} months: the burn plan {verdict}.")

    if pre_money:
        post = pre_money + raise_
        stake = raise_ / post
        low, high = USUAL_ROUND_STAKE
        print(f"  Pre-money {money(pre_money)} + raise = post-money {money(post)}; new investors own {pct(stake)}.")
        print(f"  Priced rounds commonly sell {low * 100:.0f}% to {high * 100:.0f}%; this is {where(stake, low, high)} that range.")

    if uses:
        width = max(len("Use of funds"), *(len(n) for n, _ in uses))
        print(f"  {'Use of funds':<{width}}  {'Amount':>12}  {'Share':>6}")
        for name, amount in uses:
            print(f"  {name:<{width}}  {money(amount):>12}  {pct(amount / raise_):>6}")
        total = sum(amount for _, amount in uses)
        line = f"  {'Total':<{width}}  {money(total):>12}  {pct(total / raise_):>6}"
        if abs(total / raise_ - 1) <= ROUNDING_TOLERANCE:
            print(line + "  adds up to the raise")
        else:
            side = "more than" if total > raise_ else "short of"
            print(line + f"  {money(abs(total - raise_))} {side} the raise")


def growth(args):
    start = number(args.start, "--start")
    end = number(args.end, "--end")
    periods = number(args.periods, "--periods")
    if start <= 0 or end < 0:
        fail("--start must be positive and --end zero or more")
    if periods <= 0:
        fail("--periods must be positive")
    claimed = None
    if args.claimed_rate is not None:
        claimed = share(args.claimed_rate, "--claimed-rate")
        if claimed <= -1:
            fail("--claimed-rate must be above -100%")
    unit = args.per
    multiple = end / start
    rate = multiple ** (1 / periods) - 1
    print(f"Growth from {money(start)} to {money(end)} over {periods_text(periods, unit)}: {multiple:,.2f}x")
    line = f"  Compound growth: {pct(rate)} a {unit}"
    if unit != "year":
        line += f"  (equivalent to {pct((1 + rate) ** PERIODS_PER_YEAR[unit] - 1)} a year)"
    print(line)
    if claimed is not None:
        if abs(claimed - rate) < 0.0005:
            print(f"  Deck claims {pct(claimed)} a {unit}: matches the start and end figures.")
        else:
            implied_end = start * (1 + claimed) ** periods
            print(f"  Deck claims {pct(claimed)} a {unit}: {periods_text(periods, unit)} at that rate would turn"
                  f" {money(start)} into {money(implied_end)}, not {money(end)}.")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # Segment names can hold characters the console cannot show: print "?" rather than crash.
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    m = sub.add_parser("market", help="bottom-up TAM, SAM and SOM from customer counts and prices")
    m.add_argument("--segment", nargs="+", action="append", metavar="VALUE",
                   help="NAME CUSTOMERS PRICE [SERVICEABLE]; repeat for each customer group")
    m.add_argument("--monthly", action="store_true", help="prices are per month, not per year")
    m.add_argument("--som-share", help="share of SAM the company can win in the plan period, e.g. 3%%")
    m.add_argument("--claimed-tam", help="TAM the deck quotes, to compare")
    m.add_argument("--claimed-sam", help="SAM the deck quotes, to compare")
    m.add_argument("--claimed-som", help="SOM the deck quotes, to compare")
    m.add_argument("--revenue-target", help="annual revenue in the last year of the deck's plan")
    m.set_defaults(run=market)

    r = sub.add_parser("runway", help="months of runway from the raise and the burn plan, and use of funds")
    r.add_argument("--raise", dest="raise_", required=True, help="amount being raised")
    r.add_argument("--burn", required=True, help="monthly net burn: 60000, or phases 60000:6,85000")
    r.add_argument("--cash", default="0", help="cash in the bank before the raise")
    r.add_argument("--claimed-months", help="runway the deck claims, in months")
    r.add_argument("--pre-money", help="pre-money valuation, for a priced round")
    r.add_argument("--use", nargs=2, action="append", metavar=("NAME", "VALUE"),
                   help="a use of funds line: amount, or percentage of the raise like 45%%")
    r.set_defaults(run=runway)

    g = sub.add_parser("growth", help="compound growth rate between two data points")
    g.add_argument("--start", required=True, help="first value, e.g. MRR at the start")
    g.add_argument("--end", required=True, help="last value")
    g.add_argument("--periods", required=True, help="number of periods between them")
    g.add_argument("--per", choices=sorted(PERIODS_PER_YEAR), default="month", help="period length")
    g.add_argument("--claimed-rate", help="growth rate the deck claims per period, e.g. 40%%")
    g.set_defaults(run=growth)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
