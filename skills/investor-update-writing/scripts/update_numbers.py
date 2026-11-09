#!/usr/bin/env python3
"""Numbers for an investor update: KPI table, net burn, runway and burn multiple.

Reads a small JSON file with this period's and last period's figures and prints
a Markdown KPI table with absolute and % changes (percentage points for
percentages), the comparison with plan, the metrics that got worse or are
behind plan, and cash, net burn, runway and burn multiple. Claude pastes these
figures into the update instead of doing any arithmetic itself.

Standard library only and no network, so it runs in the Claude API sandbox, on
claude.ai and in Claude Code.

Usage:
  python scripts/update_numbers.py metrics.json

JSON fields (see assets/example-metrics.json):
  company            optional, for the heading
  currency           optional symbol or code for money, e.g. "$", "₹", "EUR"
  period             label of this period, e.g. "October 2026" or "Q3 2026"
  previous_period    label of the period compared with
  months_in_period   1 for a monthly update (default), 3 for a quarterly one
  kpis               list of {name, unit, this, last, plan?, higher_is_better?, decimals?}
                     unit: money | count | percent | ratio | months
                     percent values are fractions: 0.04 means 4%
                     higher_is_better defaults to false for names containing
                     churn, burn, CAC, payback, cost or expense (but not LTV:CAC),
                     and to true otherwise.
                     A KPI named "MRR" or "ARR" is used for the burn multiple.
  cash               optional {this, last?, raised?}: cash at the end of each
                     period and money raised from investors or lenders in this one
  operating          optional {revenue, expenses}: totals for this period

Net burn per month = (expenses - revenue) / months_in_period, or, without
"operating", (cash last - cash this + raised) / months_in_period.
Runway (months) = cash this / net burn per month, with burn held flat.
Burn multiple = net burn over the period / net new ARR over the period.
"""
import json
import re
import sys

UNITS = ("money", "count", "percent", "ratio", "months")
DEFAULT_DECIMALS = {"money": 0, "count": 0, "percent": 1, "ratio": 1, "months": 1}
LOWER_IS_BETTER = re.compile(r"churn|burn|\bcac\b|payback|cost|expense", re.IGNORECASE)
HIGHER_ANYWAY = re.compile(r"\bltv\b", re.IGNORECASE)  # LTV:CAC contains "CAC" but higher is better
# Churn and margins are shares of a whole, so as fractions they cannot pass 1.
SHARE_OF_WHOLE = re.compile(r"churn|margin", re.IGNORECASE)
# A percent fraction above this (1,000%) is almost certainly a whole-number percentage.
MAX_PERCENT_FRACTION = 10
MONTHS_PER_YEAR = 12


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(2)


def signed(x, decimals):
    """Format with an explicit + or -, and no sign (and no -0) when it rounds to zero."""
    if round(x, decimals) == 0:
        return f"{0:,.{decimals}f}"
    return f"{x:+,.{decimals}f}"


def number(value, where, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"{where} must be a number, not {json.dumps(value)}")
    if minimum is not None and value < minimum:
        fail(f"{where} cannot be below {minimum:g} (is {value:g})")
    return float(value)


class Formatter:
    def __init__(self, currency):
        self.currency = currency or ""

    def money(self, x, decimals, signed=False):
        if round(x, decimals) == 0:
            x = 0.0
        sign = "-" if x < 0 else ("+" if signed and x > 0 else "")
        body = f"{abs(x):,.{decimals}f}"
        cur = self.currency
        if len(cur) > 1 and cur.isalpha():
            cur += " "
        return f"{sign}{cur}{body}"

    def value(self, kpi, x, sign=False):
        unit, d = kpi["unit"], kpi["decimals"]
        if unit == "money":
            return self.money(x, d, sign)
        if unit == "percent":
            return (signed(x * 100, d) if sign else f"{x * 100:,.{d}f}") + "%"
        text = signed(x, d) if sign else f"{x:,.{d}f}"
        if unit == "ratio":
            return text + "x"
        if unit == "months":
            return text + " mo"
        return text

    def change(self, kpi, new, old):
        """Absolute change (pp for percentages) and % change, or '' where % is not meaningful."""
        if kpi["unit"] == "percent":
            return f"{signed((new - old) * 100, kpi['decimals'])} pp", ""
        diff = self.value(kpi, new - old, sign=True)
        rel = f"{signed((new - old) / old * 100, 1)}%" if old > 0 else ""
        return diff, rel


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except OSError as e:
        fail(f"cannot read {path}: {e.strerror}")
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e.msg} at line {e.lineno}, column {e.colno}")
    if not isinstance(data, dict):
        fail("the JSON must be an object with period, previous_period and kpis")
    for key in ("period", "previous_period"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            fail(f'"{key}" is missing: give a label such as "October 2026"')
    months = data.get("months_in_period", 1)
    if isinstance(months, bool) or not isinstance(months, int) or months < 1:
        fail('"months_in_period" must be a whole number of months: 1 for monthly, 3 for quarterly')
    data["months_in_period"] = months
    kpis = data.get("kpis")
    if not isinstance(kpis, list) or not kpis:
        fail('"kpis" must be a non-empty list of {name, unit, this, last}')
    seen = set()
    for i, k in enumerate(kpis, 1):
        if not isinstance(k, dict):
            fail(f"kpis[{i}] must be an object")
        name = k.get("name")
        if not isinstance(name, str) or not name.strip():
            fail(f"kpis[{i}] needs a name")
        where = f'KPI "{name}"'
        if name.lower() in seen:
            fail(f"{where} appears twice")
        seen.add(name.lower())
        if k.get("unit") not in UNITS:
            fail(f"{where}: unit must be one of {', '.join(UNITS)} (is {json.dumps(k.get('unit'))})")
        for field in ("this", "last"):
            if field not in k:
                fail(f'{where} needs "{field}". If last period was not measured, leave the KPI out and say so in the update')
            k[field] = number(k[field], f"{where} {field}")
        if k.get("plan") is not None:
            k["plan"] = number(k["plan"], f"{where} plan")
        if k["unit"] == "percent":
            for field in ("this", "last", "plan"):
                v = k.get(field)
                if v is None:
                    continue
                if abs(v) > MAX_PERCENT_FRACTION or (SHARE_OF_WHOLE.search(name) and v > 1):
                    fail(f"{where} {field} is {v:g}: percentages are fractions, e.g. 0.04 for 4%")
        hib = k.get("higher_is_better")
        if hib is None:
            k["higher_is_better"] = bool(HIGHER_ANYWAY.search(name)) or not LOWER_IS_BETTER.search(name)
        elif not isinstance(hib, bool):
            fail(f"{where}: higher_is_better must be true or false")
        d = k.get("decimals", DEFAULT_DECIMALS[k["unit"]])
        if isinstance(d, bool) or not isinstance(d, int) or not 0 <= d <= 4:
            fail(f"{where}: decimals must be a whole number from 0 to 4")
        k["decimals"] = d
    cash = data.get("cash")
    if cash is not None:
        if not isinstance(cash, dict) or "this" not in cash:
            fail('"cash" must be an object with "this" (cash at the end of this period)')
        for field in ("this", "last", "raised"):
            if cash.get(field) is not None:
                cash[field] = number(cash[field], f"cash.{field}", minimum=0)
    op = data.get("operating")
    if op is not None:
        if not isinstance(op, dict) or "revenue" not in op or "expenses" not in op:
            fail('"operating" must be an object with "revenue" and "expenses" for this period')
        for field in ("revenue", "expenses"):
            op[field] = number(op[field], f"operating.{field}", minimum=0)
    return data


def worse(k, new, old):
    return new < old if k["higher_is_better"] else new > old


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # currency symbols such as the rupee sign on any console
    except (AttributeError, ValueError):
        pass
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if len(sys.argv) != 2:
        fail("give one metrics JSON file, e.g. python scripts/update_numbers.py assets/example-metrics.json")
    data = load(sys.argv[1])
    fmt = Formatter(data.get("currency"))
    kpis = data["kpis"]
    months = data["months_in_period"]
    this_label, last_label = data["period"].strip(), data["previous_period"].strip()
    has_plan = any(k.get("plan") is not None for k in kpis)

    heading = f"{data['company']}: " if data.get("company") else ""
    print(f"{heading}{this_label} vs {last_label} ({months} month{'s' if months > 1 else ''})")
    print()
    head = ["Metric", this_label, last_label, "Change", "% change"] + (["Plan", "vs plan"] if has_plan else [])
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    worse_lines, behind_lines = [], []
    for k in kpis:
        diff, rel = fmt.change(k, k["this"], k["last"])
        cells = [k["name"], fmt.value(k, k["this"]), fmt.value(k, k["last"]), diff, rel]
        if worse(k, k["this"], k["last"]):
            worse_lines.append(f"{k['name']} {diff}" + (f" ({rel})" if rel else ""))
        if has_plan:
            plan = k.get("plan")
            if plan is None:
                cells += ["", ""]
            else:
                pdiff, prel = fmt.change(k, k["this"], plan)
                cells += [fmt.value(k, plan), pdiff + (f" ({prel})" if prel else "")]
                if worse(k, k["this"], plan):
                    behind_lines.append(f"{k['name']} {pdiff}" + (f" ({prel})" if prel else ""))
        print("| " + " | ".join(cells) + " |")
    print()
    print("Worse than last period: " + ("; ".join(worse_lines) if worse_lines else "none"))
    if has_plan:
        print("Behind plan: " + ("; ".join(behind_lines) if behind_lines else "none"))

    cash, op = data.get("cash"), data.get("operating")
    money = lambda x: fmt.money(x, 0)
    print()
    print("Cash and runway")
    if cash is None and op is None:
        print('  Not computed: add "cash" (and "operating" or cash.last) to get net burn and runway')
    burn_cash = burn_op = None
    if cash is not None:
        raised = cash.get("raised") or 0.0
        line = f"  Cash at the end of {this_label}: {money(cash['this'])}"
        if cash.get("last") is not None:
            line += f" ({last_label}: {money(cash['last'])}; raised in the period: {money(raised)})"
            burn_cash = (cash["last"] - cash["this"] + raised) / months
        print(line)
        if burn_cash is not None:
            print(f"  Net burn from the change in cash: {money(burn_cash)} a month")
    if op is not None:
        burn_op = (op["expenses"] - op["revenue"]) / months
        sums = f"{money(op['expenses'])} - {money(op['revenue'])}"
        if months > 1:
            sums = f"({sums}) / {months}"
        print(f"  Net burn from expenses minus revenue: {sums} = {money(burn_op)} a month")
    burn = burn_op if burn_op is not None else burn_cash
    basis = "expenses minus revenue" if burn_op is not None else "the change in cash"
    if burn_op is not None and burn_cash is not None and round(burn_op) != round(burn_cash):
        print(f"  The two burn figures differ by {money(abs(burn_op - burn_cash))} a month, usually from the timing of"
              " collections, annual prepayments or one-off payments. Say which one the update uses.")
    if burn is not None and cash is not None:
        if burn > 0:
            print(f"  Runway = {money(cash['this'])} / {money(burn)} = {cash['this'] / burn:.1f} months"
                  f" (net burn from {basis}, held flat)")
        else:
            print(f"  Not burning cash this period (net burn {money(burn)} a month): runway is not limited by burn")
    elif burn is not None:
        print('  Runway needs "cash": {"this": ...}')

    arr_kpi = next((k for k in kpis if re.match(r"^(mrr|arr)\b", k["name"].strip(), re.IGNORECASE)
                    and k["unit"] == "money"), None)
    if arr_kpi is not None and burn is not None and burn > 0:
        factor = MONTHS_PER_YEAR if arr_kpi["name"].strip().lower().startswith("mrr") else 1
        net_new_arr = (arr_kpi["this"] - arr_kpi["last"]) * factor
        label = "ARR (MRR x 12)" if factor > 1 else "ARR"
        if net_new_arr > 0:
            period_burn = burn * months
            note = "" if months >= 3 else "; one month is noisy, a quarter is the usual basis"
            print(f"  Burn multiple = {money(period_burn)} net burn / {money(net_new_arr)} net new {label}"
                  f" = {period_burn / net_new_arr:.1f}x{note}")
        else:
            print(f"  Burn multiple: not meaningful, {label} did not grow this period")

    print()
    print("Percentage metrics change in percentage points (pp). % change is blank where it is not meaningful"
          " (percentages, or a zero or negative base).")


if __name__ == "__main__":
    main()
