---
name: cap-table-modeling
description: Builds a startup cap table from the founders' shares, options, SAFEs and convertible notes and models the next priced round. Converts post-money and pre-money SAFEs (valuation cap and discount, MFN clauses flagged) and convertible notes (principal plus simple interest, cap and discount), tops up the option pool to the investors' post-money target, issues the new investors' shares, and prints a before-and-after table by holder with share counts and fully diluted percentages, the price per share and the effective pre-money valuation. Use when a founder asks who will own what after a seed or Series A round, how much a SAFE or note converts into, how much dilution to expect, what the option pool shuffle costs, whether a cap or a discount applies, or shares a cap table, SAFE, convertible note or term sheet and wants a pro forma cap table.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/cap-table-modeling
---

# Cap table modelling

Turn the founders' cap table and their SAFEs and notes into a pro forma cap table for the next priced round: who owns what before and after, the price per share and the effective pre-money. The script does every calculation; your job is to read the documents correctly, get the inputs right and explain the result. The output is a model to check the lawyers' closing cap table against, not legal or tax advice. Say so once, at the end.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Collect the holders, the pool, every SAFE and note, and the round terms
- [ ] 2. Write the cap table JSON
- [ ] 3. Run scripts/cap_table.py and fix any error it reports
- [ ] 4. Run the what-ifs the founders care about
- [ ] 5. Write the answer in the output format below
- [ ] 6. Check every figure against the script output
```

### 1. Collect the inputs

- **Holders**: everyone with issued shares, plus granted options (vested or not) as their own row. Fully diluted means all of them count.
- **Unallocated pool**: option shares reserved but not yet granted.
- **Every SAFE and note**: type (post-money SAFE, pre-money SAFE or note), amount, cap, discount, MFN clause, and for notes the interest rate, issue date and maturity. [references/conversion-rules.md](references/conversion-rules.md) explains each field and what to look for in the documents.
- **The round**: headline pre-money, new money, the pool target (unallocated pool after the round as a share of the fully diluted company) and the expected closing date.

Never guess a cap, a discount, or whether a SAFE is pre-money or post-money: ask. If the founders only have percentages, use 10,000,000 shares split by those percentages and say the share counts are illustrative. If the round is not priced yet, ask for the range they expect and model its ends.

### 2. Write the JSON

Copy [assets/example-cap-table.json](assets/example-cap-table.json) and replace its contents. Mark each founder with `"founder": true` so the script prints their combined stake. Fractions are decimals (0.2 for 20%), dates are YYYY-MM-DD, every name is unique, and the file uses one currency. The script rejects unknown fields, so a typo fails loudly.

### 3. Run the model

```bash
python scripts/cap_table.py cap-table.json
```

If it exits with an error, fix the input it names and run it again. Do not estimate instead: the price, pool top-up and conversions depend on each other, and the script solves them together.

### 4. Run the what-ifs

```bash
# A lower or higher round: shows where a cap stops applying or a discount takes over
python scripts/cap_table.py cap-table.json --pre-money 10000000 --raise 2500000

# A pool sized to the hiring plan instead of the term sheet's target
python scripts/cap_table.py cap-table.json --pool-target 0.08

# Conversions priced outside the pre-money, so they dilute the new investors too
python scripts/cap_table.py cap-table.json --conversions-outside-pre-money
```

Pick the what-ifs that answer the founders' question; two or three is usually enough. If the script notes an MFN clause with better later terms and the clause applies, copy those terms into that instrument, rerun, and show both results.

### 5. Output format

```markdown
# Cap table: [Company], [round]

## The headline
Two or three sentences: the founders' combined stake before and after, the price per share, and the effective pre-money against the headline.

## Before and after
| Holder | Shares before | % before | Shares after | % after |
|---|---|---|---|---|
Every row from the script, totals included.

## How each SAFE and note converts
| Instrument | Converting amount | Converts at | Shares | % after |
|---|---|---|---|---|
One sentence for any instrument that converts at its discount or the round price instead of its cap, and for any MFN clause.

## Where the headline pre-money went
The script's breakdown: today's holders, the pool top-up and the conversions, each in currency.

## What-ifs
One line per extra run: what changed and the founders' combined stake after.

## Check with your lawyer
The assumptions this model made (which share count each cap divides into, simple interest, MFN not applied) and the terms to confirm.
```

### 6. Check before sending

- Every number appears in the script output or the documents. Percentages are copied, never recomputed.
- Pre-money and post-money are never mixed up. A post-money SAFE's cap is a post-money figure; a priced round's headline is usually pre-money.
- Each instrument's type matches its document, and the answer says which share count each cap divided into.
- The answer ends with: "This is a model to check against your lawyers' closing cap table, not legal or tax advice."

## How the script models a round

- Round price = pre-money / pre-money fully diluted shares. By default that count includes the pool top-up and every conversion, so the new investors own exactly raise / post-money and today's holders pay for the pool and the conversions.
- Each SAFE or note converts at the lowest of its cap price, its discount price and the round price: one of them, never both cap and discount.
- A post-money SAFE's stake is fixed at amount / cap of the pre-round shares plus all conversions, so later SAFEs dilute the founders, not it. A pre-money SAFE or note divides its cap by the pre-round shares plus the pool top-up, so each further SAFE or note dilutes it too.
- The pool top-up brings the unallocated pool up to the target, counting any existing unallocated pool.
- Effective pre-money = round price x today's fully diluted shares: the headline minus what the pool top-up and the conversions take.

## Rules

- Explain dilution in shares as well as percentages: nobody's share count falls in a round, but everyone's percentage does.
- When several SAFEs or notes stack up, show their combined stake after the round. That total is what usually surprises founders.
- For Indian rounds, read the Indian section of [references/conversion-rules.md](references/conversion-rules.md) before modelling CCPS, an iSAFE or a convertible note.
- Do not tell the founders whether to accept a round or a cap. Show what each option does to their stake.
