#!/usr/bin/env python3
"""SaaS metrics from a customer-by-month MRR export.

Prints, for each month: the MRR bridge (new, reactivation, expansion,
contraction, churned), ending MRR, ARR, customers, logo churn, gross revenue
churn, net and gross revenue retention and ARPA. Optional inputs add CAC, LTV,
LTV:CAC, CAC payback, runway, burn multiple and the Rule of 40.

Standard library only and no network, so it runs in the Claude API sandbox, on
claude.ai and in Claude Code.

Usage:
  python scripts/saas_metrics.py FILE.csv [--last 6] [--detail 2026-10]
      [--customer-col NAME] [--month-col NAME] [--mrr-col NAME] [--delimiter ";"]
      [--spend 3000] [--spend-months 1] [--new-customers 2]
      [--gross-margin 0.8] [--churn 0.03]
      [--cash 150000] [--net-burn 9000] [--growth 0.6] [--margin -0.25]

Input (long format): one row per customer and month. Headers are matched
ignoring case, spaces and hyphens:
  customer  customer_id, customer, customer_name, account, account_id, client, client_id
  month     month, period, billing_month, date
  mrr       mrr, monthly_recurring_revenue, mrr_amount, recurring_revenue
Any other header: name it with --customer-col, --month-col or --mrr-col.
Wide format also works and is detected automatically: one row per customer,
one column per month (headers such as 2026-01, Jan 2026 or Jan-26).

Months: YYYY-MM, YYYY-MM-DD, YYYY/MM, MM/YYYY, Jan 2026, January 2026, Jan-26.
Full dates with the day first or last (10/01/2026) are refused as ambiguous.
A customer with no row, or a blank cell, in a month has zero MRR that month.
Several rows for one customer and month (several subscriptions) are added up.
Rows whose customer is "Total" or "Grand total" are skipped.
MRR must already be monthly and recurring: divide annual plans by 12 and leave
out one-off fees, services and taxes before running.

Rates are fractions: --gross-margin 0.8 means 80%, --margin -0.25 means -25%.
"""
import argparse
import csv
import io
import math
import re
import sys

ALIASES = {
    "customer": ["customer_id", "customer", "customer_name", "account", "account_id", "client", "client_id"],
    "month": ["month", "period", "billing_month", "date"],
    "mrr": ["mrr", "monthly_recurring_revenue", "mrr_amount", "recurring_revenue"],
}
FLAGS = {"customer": "--customer-col", "month": "--month-col", "mrr": "--mrr-col"}
MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]
TOTAL_ROWS = {"total", "grand total", "totals", "sum"}
# Rule of 40: growth % + profit margin % should reach 40 (StartupReader's rule-of-40 explainer).
RULE_OF_40 = 40.0
# Burn multiple is measured over a quarter, as in StartupReader's burn-multiple explainer.
BURN_MULTIPLE_MONTHS = 3
MONTHS_PER_YEAR = 12  # ARR = MRR x 12; annual churn compounds 12 monthly rates
# A --growth or --margin fraction above this (1,000%) is almost certainly a whole-number percentage.
MAX_FRACTION = 10


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def money(x):
    if x is None:
        return "n/a"
    return f"{x:,.0f}"


def pct(x, places=1):
    return "n/a" if x is None else f"{x * 100:.{places}f}%"


def norm(header):
    return re.sub(r"[\s\-]+", "_", header.strip().lower())


def parse_month(text):
    """Return 'YYYY-MM' for a month or date string, or None if it is not one."""
    s = text.strip()
    m = re.match(r"^(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?(?:[T ].*)?$", s)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
    else:
        m = re.match(r"^(\d{1,2})[-/.](\d{4})$", s)
        if m:
            year, month = int(m.group(2)), int(m.group(1))
        else:
            m = re.match(r"^([A-Za-z]{3,9})\.?[\s,'\-]*(\d{4}|\d{2})$", s)
            if not m:
                return None
            name = m.group(1).lower()
            matches = [i for i, full in enumerate(MONTH_NAMES, 1) if full.startswith(name)]
            if len(matches) != 1:
                return None
            month = matches[0]
            year = int(m.group(2))
            if year < 100:
                year += 2000  # spreadsheet headers such as Jan-26 mean January 2026
    if not 1 <= month <= 12:
        return None
    return f"{year:04d}-{month:02d}"


def is_ambiguous_date(text):
    return re.match(r"^\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}$", text.strip()) is not None


def parse_amount(text, where):
    s = text.strip()
    if s in ("", "-"):
        return 0.0
    s = re.sub(r"[\s,$₹€£]", "", s)
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        value = float(s)
    except ValueError:
        fail(f"{where}: MRR '{text.strip()}' is not a number")
    if not math.isfinite(value):
        fail(f"{where}: MRR '{text.strip()}' is not a number")
    if value < 0:
        fail(f"{where}: MRR is negative ({text.strip()}). Credits and refunds are not MRR: "
             "net them into that customer's MRR for the month, or remove the row")
    return value


def month_range(first, last):
    y, m = int(first[:4]), int(first[5:])
    out = []
    while True:
        key = f"{y:04d}-{m:02d}"
        out.append(key)
        if key == last:
            return out
        m += 1
        if m == 13:
            y, m = y + 1, 1


def read_text(path):
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        fail(f"cannot read {path}: {e.strerror}")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    fail(f"{path} is not UTF-8 or Windows-1252 text; save it as UTF-8 CSV")


def find_column(kind, headers, given):
    normed = [norm(h) for h in headers]
    if given:
        if norm(given) in normed:
            return normed.index(norm(given))
        fail(f"{FLAGS[kind]} '{given}' is not a column. Found headers: {', '.join(headers)}")
    for alias in ALIASES[kind]:
        if alias in normed:
            return normed.index(alias)
    return None


def load(args):
    """Return ({(customer, month): mrr}, notes)."""
    text = read_text(args.file)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        fail(f"{args.file} is empty")
    delimiter = args.delimiter
    if not delimiter:
        delimiter = max([",", ";", "\t"], key=lines[0].count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    rows = [(i + 1, r) for i, r in enumerate(rows) if any(cell.strip() for cell in r)]
    if len(rows) < 2:
        fail(f"{args.file} needs a header row and at least one data row")
    headers = [h.strip() for h in rows[0][1]]
    data = rows[1:]
    notes = []

    cust = find_column("customer", headers, args.customer_col)
    month_col = find_column("month", headers, args.month_col)
    mrr_col = find_column("mrr", headers, args.mrr_col)
    values = {}
    merged = 0
    skipped_totals = 0

    def add(customer, month, amount):
        nonlocal merged
        key = (customer, month)
        if key in values:
            merged += 1
        values[key] = values.get(key, 0.0) + amount

    month_headers = {i: parse_month(h) for i, h in enumerate(headers) if i != cust}
    month_headers = {i: k for i, k in month_headers.items() if k}
    wide = month_col is None and len(month_headers) >= 2 and not args.month_col

    if wide:
        if cust is None:
            if parse_month(headers[0]):
                fail(f"no customer column. Found headers: {', '.join(headers)}. Name it with --customer-col")
            cust = 0
        keys = list(month_headers.values())
        if len(set(keys)) != len(keys):
            fail("two month columns are the same month: " + ", ".join(sorted({k for k in keys if keys.count(k) > 1})))
        ignored = [h for i, h in enumerate(headers) if i != cust and i not in month_headers]
        notes.append(f"Read as a wide table: one column per month, customers in '{headers[cust]}'.")
        if ignored:
            notes.append("Ignored columns that are not months: " + ", ".join(ignored) + ".")
        for line, row in data:
            name = row[cust].strip() if cust < len(row) else ""
            if name.lower() in TOTAL_ROWS:
                skipped_totals += 1
                continue
            if not name:
                fail(f"row {line}: the customer is blank")
            for i, key in month_headers.items():
                cell = row[i] if i < len(row) else ""
                add(name, key, parse_amount(cell, f"row {line}, column '{headers[i]}'"))
    else:
        for kind, col in (("customer", cust), ("month", month_col), ("mrr", mrr_col)):
            if col is None:
                fail(f"no {kind} column. Found headers: {', '.join(headers)}. "
                     f"Name it with {FLAGS[kind]}, e.g. {FLAGS[kind]} \"{headers[0]}\"")
        for line, row in data:
            cells = row + [""] * (len(headers) - len(row))
            name = cells[cust].strip()
            if name.lower() in TOTAL_ROWS:
                skipped_totals += 1
                continue
            if not name:
                fail(f"row {line}: the customer is blank")
            raw_month = cells[month_col]
            key = parse_month(raw_month)
            if key is None:
                if is_ambiguous_date(raw_month):
                    fail(f"row {line}: '{raw_month.strip()}' could be day/month or month/day. "
                         "Convert the month column to YYYY-MM")
                fail(f"row {line}: cannot read the month '{raw_month.strip()}'. Use YYYY-MM, e.g. 2026-01")
            add(name, key, parse_amount(cells[mrr_col], f"row {line}"))

    if merged:
        notes.append(f"{merged} row(s) repeated a customer and month already seen; their MRR was added together.")
    if skipped_totals:
        notes.append(f"Skipped {skipped_totals} total row(s).")
    if not values:
        fail("no data rows")
    # Round sums so float noise from adding rows never looks like expansion or contraction.
    return {k: round(v, 6) for k, v in values.items()}, notes


def compute(values):
    months_present = sorted({m for _, m in values})
    months = month_range(months_present[0], months_present[-1])
    missing = [m for m in months if m not in months_present]
    if missing:
        fail("no rows at all for " + ", ".join(missing) + ". Months must be consecutive; if the company "
             "really had no revenue then, add a row with MRR 0 for that month")
    if len(months) < 2:
        fail(f"only one month ({months[0]}) in the file: the bridge needs at least two")
    customers = sorted({c for c, _ in values})

    def val(c, i):
        return values.get((c, months[i]), 0.0)

    rows = []
    for i in range(1, len(months)):
        r = {"month": months[i], "new": 0.0, "reactivation": 0.0, "expansion": 0.0, "contraction": 0.0,
             "churned": 0.0, "n_new": 0, "n_react": 0, "n_lost": 0, "n_start": 0, "n_end": 0,
             "movers": {"New": [], "Reactivation": [], "Expansion": [], "Contraction": [], "Churned": []}}
        r["start"] = sum(val(c, i - 1) for c in customers)
        r["end"] = sum(val(c, i) for c in customers)
        for c in customers:
            p, q = val(c, i - 1), val(c, i)
            r["n_start"] += p > 0
            r["n_end"] += q > 0
            if p == 0 and q > 0:
                if any(val(c, j) > 0 for j in range(i - 1)):
                    r["reactivation"] += q
                    r["n_react"] += 1
                    r["movers"]["Reactivation"].append((c, q))
                else:
                    r["new"] += q
                    r["n_new"] += 1
                    r["movers"]["New"].append((c, q))
            elif p > 0 and q == 0:
                r["churned"] += p
                r["n_lost"] += 1
                r["movers"]["Churned"].append((c, p))
            elif q > p:
                r["expansion"] += q - p
                r["movers"]["Expansion"].append((c, q - p))
            elif q < p:
                r["contraction"] += p - q
                r["movers"]["Contraction"].append((c, p - q))
        r["net_new"] = r["new"] + r["reactivation"] + r["expansion"] - r["contraction"] - r["churned"]
        assert abs(r["start"] + r["net_new"] - r["end"]) < 1e-6
        start = r["start"]
        kept = start - r["contraction"] - r["churned"]
        r["growth"] = r["net_new"] / start if start > 0 else None
        r["arr"] = r["end"] * MONTHS_PER_YEAR
        r["logo_churn"] = r["n_lost"] / r["n_start"] if r["n_start"] else None
        r["gross_revenue_churn"] = (r["contraction"] + r["churned"]) / start if start > 0 else None
        r["nrr"] = (kept + r["expansion"]) / start if start > 0 else None
        r["grr"] = kept / start if start > 0 else None
        r["arpa"] = r["end"] / r["n_end"] if r["n_end"] else None
        rows.append(r)
    return months, customers, val, rows


def print_table(rows, opening):
    lines = [
        ("Starting MRR", lambda r: money(r["start"])),
        ("+ New", lambda r: money(r["new"])),
        ("+ Reactivation", lambda r: money(r["reactivation"])),
        ("+ Expansion", lambda r: money(r["expansion"])),
        ("- Contraction", lambda r: money(r["contraction"])),
        ("- Churned", lambda r: money(r["churned"])),
        ("= Net new MRR", lambda r: money(r["net_new"])),
        ("Ending MRR", lambda r: money(r["end"])),
        ("MRR growth", lambda r: pct(r["growth"])),
        ("ARR (MRR x 12)", lambda r: money(r["arr"])),
        ("Customers (end)", lambda r: str(r["n_end"])),
        ("  new / back / lost", lambda r: f"{r['n_new']}/{r['n_react']}/{r['n_lost']}"),
        ("Logo churn", lambda r: pct(r["logo_churn"])),
        ("Gross revenue churn", lambda r: pct(r["gross_revenue_churn"])),
        ("Net revenue retention", lambda r: pct(r["nrr"])),
        ("Gross revenue retention", lambda r: pct(r["grr"])),
        ("ARPA", lambda r: money(r["arpa"])),
    ]
    cells = [[fn(r) for r in rows] for _, fn in lines]
    width = max(len(r["month"]) for r in rows)
    width = max([width] + [len(c) for row in cells for c in row]) + 2
    label = max(len(name) for name, _ in lines) + 1
    print(f"Opening month {opening}")
    print(f"{'MRR bridge':<{label}}" + "".join(f"{r['month']:>{width}}" for r in rows))
    for (name, _), row in zip(lines, cells):
        print(f"{name:<{label}}" + "".join(f"{c:>{width}}" for c in row))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="CSV of MRR by customer and month")
    parser.add_argument("--customer-col", help="header of the customer column")
    parser.add_argument("--month-col", help="header of the month column")
    parser.add_argument("--mrr-col", help="header of the MRR column")
    parser.add_argument("--delimiter", help="field separator (default: guessed from the header: , ; or tab)")
    parser.add_argument("--last", type=int, help="show only the last N months in the table (summaries use the whole file)")
    parser.add_argument("--detail", metavar="YYYY-MM", help="list each customer's movement in this month")
    parser.add_argument("--spend", type=float, help="sales and marketing spend over the last --spend-months months")
    parser.add_argument("--spend-months", type=int, default=1, help="months the spend covers, ending with the latest (default 1)")
    parser.add_argument("--new-customers", type=int, help="customers won in those months (default: new customers in the file)")
    parser.add_argument("--gross-margin", type=float, help="gross margin as a fraction, e.g. 0.8")
    parser.add_argument("--churn", type=float, help="monthly churn for LTV as a fraction (default: average monthly logo churn)")
    parser.add_argument("--cash", type=float, help="cash in the bank now")
    parser.add_argument("--net-burn", type=float, help="average monthly net burn over recent months (expenses minus revenue)")
    parser.add_argument("--growth", type=float, help="revenue or ARR growth over the last 12 months as a fraction, for the Rule of 40")
    parser.add_argument("--margin", type=float, help="EBITDA or free cash flow margin as a fraction (negative for a loss), for the Rule of 40")
    args = parser.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # customer names and headers may not be ASCII
    except (AttributeError, ValueError):
        pass

    for flag in ("gross_margin", "churn"):
        v = getattr(args, flag)
        if v is not None and not 0 < v <= 1:
            fail(f"--{flag.replace('_', '-')} must be a fraction between 0 and 1, e.g. 0.8 for 80%")
    for flag in ("spend", "cash"):
        v = getattr(args, flag)
        if v is not None and v < 0:
            fail(f"--{flag.replace('_', '-')} cannot be negative")
    if args.last is not None and args.last < 1:
        fail("--last must be at least 1")
    if args.spend_months < 1:
        fail("--spend-months must be at least 1")
    if args.new_customers is not None and args.new_customers < 0:
        fail("--new-customers cannot be negative")
    for flag in ("growth", "margin"):
        v = getattr(args, flag)
        if v is not None and abs(v) > MAX_FRACTION:
            fail(f"--{flag} looks like a percentage: give a fraction, e.g. 0.6 for 60%")

    values, notes = load(args)
    months, customers, val, rows = compute(values)
    last = rows[-1]
    detail = None
    if args.detail:
        key = parse_month(args.detail)
        detail = next((r for r in rows if r["month"] == key), None)
        if detail is None:
            fail(f"--detail {args.detail}: not a month with movements in the file ({months[1]} to {months[-1]})")

    print(f"SaaS metrics: {len(customers)} customers, {len(months)} months ({months[0]} to {months[-1]}). "
          "Amounts in the file's currency.")
    for note in notes:
        print(f"Note: {note}")
    shown = rows[-args.last:] if args.last else rows
    opening = months[months.index(shown[0]["month"]) - 1]
    n = shown[0]["n_start"]
    print_table(shown, f"{opening}: MRR {money(shown[0]['start'])}, {n} customer{'' if n == 1 else 's'}")

    # Over the last 12 months, or the whole file if shorter.
    window = min(MONTHS_PER_YEAR, len(rows))
    base = len(months) - 1 - window
    cohort = [c for c in customers if val(c, base) > 0]
    cohort_start = sum(val(c, base) for c in cohort)
    period = rows[-window:]
    churn_rates = [r["logo_churn"] for r in period if r["logo_churn"] is not None]
    avg_churn = sum(churn_rates) / len(churn_rates) if churn_rates else None
    label = "last 12 months" if window == MONTHS_PER_YEAR else f"last {window} months (a 12-month figure needs 13 months of data)"
    print()
    print(f"Over the {label}, {months[base]} to {months[-1]}")
    start_mrr, end_mrr = rows[-window]["start"], last["end"]
    if start_mrr > 0:
        cmgr = (end_mrr / start_mrr) ** (1 / window) - 1 if end_mrr > 0 else None
        print(f"  MRR {money(start_mrr)} to {money(end_mrr)}: {pct(end_mrr / start_mrr - 1)}"
              f" ({pct(cmgr)} a month, compounded)")
    if avg_churn is not None:
        print(f"  Average monthly logo churn {pct(avg_churn, 2)}, about {pct(1 - (1 - avg_churn) ** MONTHS_PER_YEAR)} a year compounded")
    if cohort_start > 0:
        now = sum(val(c, len(months) - 1) for c in cohort)
        kept = sum(min(val(c, len(months) - 1), val(c, base)) for c in cohort)
        print(f"  Customers paying in {months[base]} ({len(cohort)}): NRR {pct(now / cohort_start)}, GRR {pct(kept / cohort_start)}")

    if detail is not None:
        print()
        print(f"Customer movements in {detail['month']}")
        for kind, items in detail["movers"].items():
            items = sorted(items, key=lambda x: (-x[1], x[0]))
            print(f"  {kind:<13}" + (", ".join(f"{c} {money(v)}" for c, v in items) if items else "none"))

    # Unit economics: the formulas of StartupReader's LTV and CAC calculator.
    if args.spend is not None or args.gross_margin is not None:
        print()
        print(f"Unit economics ({last['month']})")
        cac = None
        if args.spend is not None:
            k = min(args.spend_months, len(rows))
            won = args.new_customers if args.new_customers is not None else sum(r["n_new"] for r in rows[-k:])
            window_label = rows[-k]["month"] + ("" if k == 1 else f" to {last['month']}")
            source = f"given, {window_label}" if args.new_customers is not None else f"new in {window_label}"
            if won > 0:
                cac = args.spend / won
                print(f"  CAC = {money(args.spend)} spend / {won} customers ({source}) = {money(cac)}")
            else:
                print(f"  CAC: not defined, no new customers ({source})")
        if args.gross_margin is not None and last["arpa"]:
            gp = last["arpa"] * args.gross_margin
            churn = args.churn if args.churn is not None else avg_churn
            churn_source = "given" if args.churn is not None else "average monthly logo churn"
            print(f"  Monthly gross profit per customer = ARPA {money(last['arpa'])} x {args.gross_margin:g} = {money(gp)}")
            ltv = None
            if churn:
                ltv = gp / churn
                print(f"  LTV = {money(gp)} / {pct(churn, 2)} monthly churn ({churn_source}) = {money(ltv)}")
            else:
                print("  LTV: not defined, no churn in the period (give --churn to estimate it)")
            if cac:
                if ltv:
                    print(f"  LTV:CAC = {ltv / cac:.1f}:1")
                print(f"  CAC payback = {money(cac)} / {money(gp)} = {cac / gp:.1f} months")
        elif args.gross_margin is None:
            print("  LTV and CAC payback need --gross-margin (LTV uses gross profit, not revenue)")

    # Cash: StartupReader's burn rate and runway calculator and burn-multiple explainer.
    if args.cash is not None or args.net_burn is not None:
        print()
        print("Cash and efficiency")
        if args.net_burn is not None and args.net_burn > 0:
            if args.cash is not None:
                print(f"  Runway = {money(args.cash)} cash / {money(args.net_burn)} net burn = "
                      f"{args.cash / args.net_burn:.1f} months (burn held flat)")
            k = min(BURN_MULTIPLE_MONTHS, len(rows))
            nn_arr = (last["end"] - rows[-k]["start"]) * MONTHS_PER_YEAR
            burn = args.net_burn * k
            if nn_arr > 0:
                print(f"  Burn multiple ({k} months) = {money(burn)} net burn / {money(nn_arr)} net new ARR = {burn / nn_arr:.1f}x")
            else:
                print(f"  Burn multiple: not meaningful, ARR did not grow over the last {k} months")
        elif args.net_burn is not None:
            print(f"  Not burning cash (net burn {money(args.net_burn)}): runway is not limited by burn")
        else:
            print("  Runway and burn multiple need --net-burn")

    if args.margin is not None:
        growth = args.growth
        source = "given"
        if growth is None and window == MONTHS_PER_YEAR and rows[-window]["start"] > 0:
            growth = last["end"] / rows[-window]["start"] - 1
            source = "ARR growth over the last 12 months"
        print()
        if growth is None:
            print("Rule of 40: needs --growth (12 months of growth), or 13 months of data")
        else:
            score = (growth + args.margin) * 100
            verdict = "passes" if score >= RULE_OF_40 else "falls short"
            sign = "-" if args.margin < 0 else "+"
            print(f"Rule of 40 = {growth * 100:.1f}% growth ({source}) {sign} {abs(args.margin) * 100:.1f}% margin"
                  f" = {score:.1f}: {verdict} (the bar is {RULE_OF_40:g})")

    print()
    print("Conventions (StartupReader's ARR and MRR and churn rate calculators): rates use the start of the month.")
    print("  Logo churn = customers lost / customers at the start. Gross revenue churn = (contraction + churned) / starting MRR.")
    print("  NRR = (starting MRR + expansion - contraction - churned) / starting MRR; GRR = the same without expansion.")
    print("  Reactivation = a customer paying again after a month or more at zero; like new MRR, it is outside NRR and GRR.")


if __name__ == "__main__":
    main()
