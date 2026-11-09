---
name: saas-metrics-analysis
description: Computes SaaS metrics from a CSV of monthly recurring revenue by customer (an export from Stripe, Chargebee, another billing tool or a spreadsheet). Builds the monthly MRR bridge (new, expansion, contraction, churned and reactivation MRR) and reports ending MRR, ARR, customer count, logo churn, gross revenue churn, net revenue retention (NRR), gross revenue retention (GRR) and ARPA, then CAC, LTV, LTV:CAC, CAC payback, runway, burn multiple and the Rule of 40 when spend, gross margin and cash figures are given. A bundled script does the arithmetic and prints the definitions it uses. Use when a founder shares MRR, subscription or billing data, or asks about MRR growth, ARR, churn rate, customer churn, revenue churn, net dollar retention, expansion revenue, unit economics, LTV to CAC ratio, CAC payback, burn multiple, runway or the Rule of 40, or needs metrics for a board meeting, investor update or fundraise.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/saas-metrics-analysis
---

# SaaS metrics analysis

Turn a customer-by-month MRR export into the numbers a founder reports and investors check: where MRR came from, what leaked, and whether growth pays for itself. The script does all the arithmetic; your job is clean input, the right questions and a clear reading of the results.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Get the data into one row per customer per month
- [ ] 2. Run scripts/saas_metrics.py on it
- [ ] 3. Ask for spend, gross margin and cash figures, then run again with them
- [ ] 4. Find what drove the months that stand out (--detail)
- [ ] 5. Write the analysis in the output format below
- [ ] 6. Check every figure against the script output
```

### 1. Prepare the data

The script reads one row per customer per month with columns for customer, month and MRR, or a wide sheet with one column per month. Common header names are matched automatically; for anything else pass `--customer-col`, `--month-col` and `--mrr-col` with the exact header. Months can be `2026-01`, `2026-01-31`, `Jan 2026` or `Jan-26`.

If the export is invoices, payments or subscriptions rather than MRR per month, build that table first and save it as a CSV. Normalise annual plans to monthly, and leave out setup fees, services, trials and taxes: the rules are in [references/definitions.md](references/definitions.md). Tell the founder what you changed.

Before running, ask if anything is unclear:
- Is the amount MRR, or invoiced amounts that include annual prepayments?
- Is there more than one currency?
- Has any customer changed ID (a merger or new billing account)? That would show as one churn and one new customer.

### 2. Run the numbers

```bash
python scripts/saas_metrics.py mrr.csv
python scripts/saas_metrics.py export.csv --customer-col "Account name" --month-col "Invoice month" --mrr-col "MRR (USD)"
python scripts/saas_metrics.py assets/example-mrr.csv --last 6
```

`--last N` shows only the last N months in the table; the summaries still use the whole file (up to 12 months). If the script exits with an error, fix the input it names and run it again. Never estimate a figure instead.

### 3. Add unit economics and cash

Ask for whichever of these the founder has, then rerun with them:

| Input | Flag | Note |
|---|---|---|
| Sales and marketing spend | `--spend 6000 --spend-months 3` | All of it: salaries, tools, agencies, not only ads. Three months is steadier than one. |
| New customers won | `--new-customers 4` | Only if the file's count is wrong, e.g. free sign-ups converted later |
| Gross margin | `--gross-margin 0.8` | A fraction. Hosting, third-party APIs, payment fees and support come out of it |
| Cash and net burn | `--cash 90000 --net-burn 6000` | Net burn is the average monthly cash loss, excluding money raised |
| Growth and profit margin | `--growth 0.6 --margin -0.25` | Rule of 40 only, for scaled companies. EBITDA or free cash flow margin: ask which |

```bash
python scripts/saas_metrics.py assets/example-mrr.csv --last 4 --spend 6000 --spend-months 3 --gross-margin 0.8 --cash 90000 --net-burn 6000
```

### 4. Find the drivers

For each month where NRR drops, churn spikes or growth stalls, list who moved:

```bash
python scripts/saas_metrics.py mrr.csv --detail 2026-10
```

Name customers by the IDs in the file. One large account often explains a whole month.

### 5. Output format

```markdown
# SaaS metrics: [Company], [first month] to [last month]

## The headline
Two or three sentences: MRR and ARR now and how fast they grew, where the growth came from, and the biggest leak.

## MRR bridge
The last three to six months from the script's table: starting MRR, new, reactivation, expansion, contraction, churned, ending MRR. One sentence on the trend.

## Retention and churn
| | [month] | [month] | [month] |
|---|---|---|---|
| Logo churn | | | |
| Gross revenue churn | | | |
| NRR | | | |
| GRR | | | |
Then the cohort NRR and GRR over the period, the compounded annual churn, and which customers drove the bad months.

## Unit economics and efficiency
CAC, LTV, LTV:CAC, CAC payback, runway, burn multiple (and Rule of 40 if relevant), each with the rule of thumb from references/definitions.md and one line on what it means here.

## What to look at next
Up to three specific checks or actions, most important first.

## Definitions used
The conventions block from the script output, plus any data changes you made in step 1.
```

### 6. Check before sending

- Every number in the analysis appears in the script output or the founder's own inputs.
- With fewer than 13 months of data, the cohort NRR is not called "12-month" or "annual".
- Churn and retention say which base they use (customers or MRR at the start of the month).
- Rules of thumb are quoted as rules of thumb, from references/definitions.md only, with no invented benchmarks.

## Rules

- Keep the script's definitions. If the founder's dashboard uses another convention (churn on average customers, NRR without contraction), show both, labelled, and say why they differ. The common differences are listed in [references/definitions.md](references/definitions.md).
- With a small base, one customer moves churn by several points. Say so when a rate rests on one or two customers, and prefer the period averages to any single month.
- ARR here is run-rate ARR (MRR x 12). Do not call it revenue or contracted ARR.
- LTV from a few months of churn data is fragile. Show it, but say how many months it rests on, and suggest a cohort table once there is a year of data.
