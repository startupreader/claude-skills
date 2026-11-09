#!/usr/bin/env python3
"""Term sheet arithmetic: option pool shuffle, liquidation waterfall, anti-dilution.

Standard library only, so it runs in the Claude API sandbox (no network, no
package installs), on claude.ai and in Claude Code.

Usage:
  python scripts/term_sheet_math.py pool --pre 20000000 --raise 5000000 \
      --pool-post 0.10 --existing 7000000 [--existing-pool 0]
  python scripts/term_sheet_math.py waterfall --invested 5000000 --stake 0.20 \
      --multiple 1 --participation none|full|cap --cap 3 \
      --exits 10000000,25000000,100000000
  python scripts/term_sheet_math.py antidilution --old-price 2.5 --new-price 1.25 \
      --new-money 5000000 --broad 10000000 [--narrow 9000000] [--invested 5000000]

Amounts are in one currency unit (dollars or rupees); shares are counts.
Results are simplified models for checking a term sheet, not legal advice.
"""
import argparse
import sys


def money(x):
    return f"{x:,.0f}"


def pct(x):
    return f"{x * 100:.1f}%"


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def pool(args):
    """Investor stake and pool size are fixed on a post-money basis; the pool
    is created before the round, so its shares are priced into the pre-money."""
    if args.pre <= 0 or args.raise_ <= 0:
        fail("--pre and --raise must be positive")
    post = args.pre + args.raise_
    investor = args.raise_ / post
    if not 0 <= args.pool_post < 1 - investor:
        fail(f"--pool-post must be between 0 and {1 - investor:.3f} (the investor already takes {pct(investor)})")
    # Post-round total T: existing holders keep 1 - investor - pool of it, so
    # T = existing / (1 - investor - pool). An existing unallocated pool counts
    # toward the target, so only the shortfall is added.
    total = args.existing / (1 - investor - args.pool_post)
    top_up = args.pool_post * total - args.existing_pool
    if top_up < 0:
        print(f"Note: the existing pool is already above {pct(args.pool_post)} of post-money, so nothing is added.")
        top_up = 0.0
    pre_shares = args.existing + args.existing_pool + top_up
    price = args.pre / pre_shares
    new_shares = args.raise_ / price
    total = pre_shares + new_shares
    effective_pre = (args.existing + args.existing_pool) * price
    print("Option pool shuffle (pool created before the round, inside the pre-money)")
    print(f"  Post-money valuation:      {money(post)}")
    print(f"  Price per share:           {price:,.4f}")
    print(f"  New investor shares:       {money(new_shares)}  ({pct(new_shares / total)})")
    print(f"  Pool shares added:         {money(top_up)}")
    print(f"  Pool after round:          {money(args.existing_pool + top_up)}  ({pct((args.existing_pool + top_up) / total)})")
    print(f"  Existing holders after:    {money(args.existing)}  ({pct(args.existing / total)})")
    print(f"  Effective pre-money:       {money(effective_pre)}  (headline {money(args.pre)})")
    print(f"  Cost of the pool to existing holders: {money(args.pre - effective_pre)}")
    if top_up > 0 and args.existing_pool == 0:
        # Without the shuffle the investor buys at pre / existing, then a pool
        # of the same size dilutes everyone, the investor included.
        holders = 1 - investor
        print(f"  Same pool created after the round instead: existing holders {pct(holders * (1 - args.pool_post))},"
              f" investor {pct(investor * (1 - args.pool_post))}")


def waterfall(args):
    """One preferred class, one exit. The investor takes its preference or, if
    better, converts to common; participating preferred takes both (up to a cap)."""
    if not 0 < args.stake < 1:
        fail("--stake must be the investor's as-converted ownership, between 0 and 1")
    if args.participation == "cap" and not args.cap:
        fail("--participation cap needs --cap (total return multiple, e.g. 3)")
    try:
        exits = [float(x) for x in args.exits.split(",") if x.strip()]
    except ValueError:
        fail("--exits must be comma-separated numbers, e.g. 10000000,25000000")
    pref = args.invested * args.multiple
    if args.participation == "none":
        label = "non-participating"
    elif args.participation == "full":
        label = "fully participating"
    else:
        label = f"participating, capped at {args.cap:g}x"
    print(f"Liquidation waterfall: {args.multiple:g}x {label}, invested {money(args.invested)}, {pct(args.stake)} as converted")
    print(f"  {'Exit value':>16}  {'Investor':>14}  {'Everyone else':>14}  How the investor is paid")
    for exit_value in exits:
        converted = args.stake * exit_value
        if args.participation == "none":
            preferred = min(pref, exit_value)
            investor = max(preferred, converted)
            how = "converts to common" if converted > preferred else "takes its preference"
        elif args.participation == "full":
            preferred = min(pref, exit_value)
            investor = preferred + args.stake * (exit_value - preferred)
            how = "preference plus its share of the rest"
        else:
            preferred = min(pref, exit_value)
            capped = min(preferred + args.stake * (exit_value - preferred), args.invested * args.cap)
            investor = max(capped, converted)
            how = "converts to common" if converted > capped else ("hits the cap" if capped == args.invested * args.cap else "preference plus its share of the rest")
        print(f"  {money(exit_value):>16}  {money(investor):>14}  {money(exit_value - investor):>14}  {how}")


def antidilution(args):
    """New conversion price = old price x (A + B) / (A + C).
    A = shares outstanding before the new issue (broad: everything incl. options
    and the unallocated pool; narrow: a smaller group), B = shares the new money
    would buy at the old price, C = new shares actually issued."""
    if args.new_price >= args.old_price:
        fail("anti-dilution applies only when --new-price is below --old-price")
    b = args.new_money / args.old_price
    c = args.new_money / args.new_price
    rows = [("Broad-based weighted average", args.old_price * (args.broad + b) / (args.broad + c))]
    if args.narrow:
        rows.append(("Narrow-based weighted average", args.old_price * (args.narrow + b) / (args.narrow + c)))
    rows.append(("Full ratchet", args.new_price))
    print(f"Anti-dilution: old price {args.old_price:g}, down-round price {args.new_price:g}, new money {money(args.new_money)}")
    print(f"  B (new money at old price): {money(b)} shares   C (shares actually issued): {money(c)}")
    if args.invested:
        before = args.invested / args.old_price
        print(f"  The investor's {money(args.invested)} converts into {money(before)} shares at the old price")
        print(f"  {'Method':<30} {'New price':>10} {'Shares as converted':>20} {'Extra shares':>13}")
    else:
        print(f"  {'Method':<30} {'New price':>10}")
    for name, price in rows:
        line = f"  {name:<30} {price:>10,.4f}"
        if args.invested:
            after = args.invested / price
            line += f" {money(after):>20} {'+' + money(after - before):>13}"
        print(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pool", help="option pool shuffle and effective pre-money")
    p.add_argument("--pre", type=float, required=True, help="headline pre-money valuation")
    p.add_argument("--raise", dest="raise_", type=float, required=True, help="amount invested in the round")
    p.add_argument("--pool-post", type=float, required=True, help="unallocated pool as a fraction of post-money, e.g. 0.10")
    p.add_argument("--existing", type=float, required=True, help="shares held by founders and earlier investors")
    p.add_argument("--existing-pool", type=float, default=0, help="unallocated pool shares that already exist")
    p.set_defaults(run=pool)

    w = sub.add_parser("waterfall", help="what the investor and everyone else get at each exit value")
    w.add_argument("--invested", type=float, required=True)
    w.add_argument("--stake", type=float, required=True, help="investor's as-converted ownership, e.g. 0.20")
    w.add_argument("--multiple", type=float, default=1.0, help="preference multiple, e.g. 1 or 2")
    w.add_argument("--participation", choices=["none", "full", "cap"], default="none")
    w.add_argument("--cap", type=float, help="total return cap as a multiple of the investment, with --participation cap")
    w.add_argument("--exits", required=True, help="comma-separated exit values")
    w.set_defaults(run=waterfall)

    a = sub.add_parser("antidilution", help="adjusted conversion price in a down round")
    a.add_argument("--old-price", type=float, required=True)
    a.add_argument("--new-price", type=float, required=True)
    a.add_argument("--new-money", type=float, required=True)
    a.add_argument("--broad", type=float, required=True, help="A for broad-based: all shares, options and pool")
    a.add_argument("--narrow", type=float, help="A for narrow-based, e.g. issued shares only")
    a.add_argument("--invested", type=float, help="the protected investor's original investment, to show extra shares")
    a.set_defaults(run=antidilution)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
