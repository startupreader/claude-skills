---
name: investor-update-writing
description: Drafts monthly or quarterly investor updates, board updates and shareholder letters from a founder's metrics and notes, in a fixed structure (a one-line TL;DR, a KPI table with changes against last period and plan, highlights, lowlights, specific asks, cash and runway, and team). A bundled script works out every change, net burn, runway and burn multiple so no figure is calculated by hand, and the writing rules keep the update numbers-first and free of hype, with bad news early and metric definitions consistent from one update to the next. Use when a founder asks for an investor update, monthly update, quarterly update, board update, shareholder or stakeholder update, or wants to report MRR, ARR, revenue, churn, burn rate, runway, hiring or fundraising progress to investors, angels or a board.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/investor-update-writing
---

# Investor update writing

Investors read updates quickly and compare them with the last one. An update earns trust when it reports the same numbers, measured the same way, every time, and when bad news arrives before anyone has to ask. Write it only from the founder's numbers and notes.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Collect this period's numbers and notes
- [ ] 2. Write the metrics JSON (same KPIs and definitions as last time)
- [ ] 3. Run scripts/update_numbers.py
- [ ] 4. Draft the update from assets/template.md
- [ ] 5. Check tone and traceability
```

### 1. Collect the inputs

Ask for everything missing in one message:
- The period (month or quarter) and the previous update, if there is one. Reuse its KPIs, their order and their definitions.
- Each KPI's value this period and last period, and the plan or target if the founder has one.
- Cash at the end of this period and the last, and any money raised in the period. If they have them, revenue and operating expenses for the period.
- Notes: wins, problems, hires and departures, and what they need from investors.

Never fill a gap with an estimate. If a KPI was not measured, leave it out and say so in the update.

**If there is a customer-level MRR export.** When the saas-metrics-analysis skill is available, run it on the export first and copy its figures exactly as printed: MRR, ARR, customers, logo churn, NRR and GRR for this month and last month from its table. For a quarterly update, take MRR, ARR and customers from the quarter-end months, add up the three months of new, expansion and churned MRR, and label any rate as monthly or as the quarter's average. Put its definitions in the update's definitions line. Without that skill, take MRR from the founder's billing tool and say which tool.

### 2. Write the metrics JSON

Copy [assets/example-metrics.json](assets/example-metrics.json) and fill it in:
- `kpis`: each with `name`, `unit` (`money`, `count`, `percent`, `ratio` or `months`), `this`, `last` and, if there is one, `plan`.
- Percentages are fractions: `0.04` is 4%.
- Names containing churn, burn, CAC, payback, cost or expense are treated as lower-is-better. For any other metric where lower is better, add `"higher_is_better": false`.
- Name the recurring revenue KPI exactly `MRR` or `ARR` so the script can work out the burn multiple.
- `cash`: `this`, `last` and `raised` (equity or debt received this period, which is not burn). `operating`: `revenue` and `expenses` as totals for the whole period.
- `months_in_period`: 1 for monthly, 3 for quarterly.

### 3. Run the numbers

```bash
python scripts/update_numbers.py metrics.json
python scripts/update_numbers.py assets/example-metrics.json
```

The script prints the KPI table in Markdown, a "Worse than last period" line, a "Behind plan" line, and cash, net burn, runway and burn multiple. Runway is cash divided by monthly net burn, with burn held flat. If it reports an error, fix the input it names and run it again. Do not work out any figure yourself.

### 4. Draft the update

Fill in [assets/template.md](assets/template.md), in this order:

1. **TL;DR**: one sentence with the most important number, the biggest problem and the top ask.
2. **Numbers**: the script's table, unchanged, then one or two sentences on what moved most and why.
3. **Highlights**: two to four bullets, each starting with a number or a named outcome.
4. **Lowlights**: everything on the "Worse than last period" and "Behind plan" lines that matters, plus problems from the notes. Say what happened, why (if known) and what the founder is doing about it.
5. **Asks**: one to three, each naming who and what. "Intros welcome" is not an ask; "an intro to a head of support at a 50 to 200 person online retailer, to test our escalation workflow" is.
6. **Cash and runway**: cash, net burn and which figure it is, and runway in months, from the script.
7. **Team**: joiners, leavers with their roles, and open roles.

End with a definitions line for every KPI. Follow the tone rules below throughout.

### 5. Check before sending

- Every number appears in the script output or the founder's notes.
- If "Worse than last period" or "Behind plan" lists a key metric, it is in the TL;DR or the lowlights.
- Each ask names a type of person or company and the action wanted.
- KPI names and definitions match the last update, or the change is stated.
- No hype words or exclamation marks.

## Tone rules

- **Numbers first.** Start bullets with the figure: "$4,974 MRR, down 1.0%", not "MRR dipped slightly".
- **No hype.** Leave out words like excited, thrilled, huge, massive, incredible, game-changing and crushing it, and exclamation marks. Let the numbers carry it.
- **Bad news early and plainly.** If a key metric fell or missed plan, the TL;DR says so. Do not soften with "slight", "temporary" or "one-off" unless the founder's notes show why.
- **Same metrics, same definitions.** Keep last update's KPIs and order. If a definition changed, say so in the update and give last period on the new basis, or say that it cannot be restated.
- **Every number traceable.** Each figure comes from the script output or the founder's notes, quoted as printed. No forecasts unless the founder gave them, labelled as their plan.
- **Short.** Investors skim. Cut anything that is not a number, a decision, a problem or an ask.
- Updates get forwarded. Name customers, candidates or partners only if the founder's notes already do.
