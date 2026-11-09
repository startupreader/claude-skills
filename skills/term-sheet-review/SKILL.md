---
name: term-sheet-review
description: Reviews a startup venture capital term sheet clause by clause and quantifies the economic terms. Works out the effective pre-money valuation after the option pool shuffle, liquidation preference payouts at several exit values and the anti-dilution adjustment in a down round, then rates each clause as founder-friendly, market standard or aggressive and lists questions for the founders' lawyer. Use when a founder shares or pastes a term sheet, a letter of intent or an investment offer, or asks about valuation, option pool, liquidation preference, participation, anti-dilution, pro-rata, board seats, protective provisions, drag-along or no-shop terms.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/term-sheet-review
---

# Term sheet review

Turn a term sheet into numbers the founders can see, then judge each clause against common practice. The output is a briefing for the founders and their lawyer, not legal advice. Say so once, at the end.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Extract the terms into the term table
- [ ] 2. Ask for any missing inputs the maths needs
- [ ] 3. Run the numbers with scripts/term_sheet_math.py
- [ ] 4. Rate every clause using references/clauses.md
- [ ] 5. Write the review in the output format below
- [ ] 6. Check every figure in the review against the script output
```

### 1. Extract the terms

Read the whole document before rating anything: a definition on page 3 can change a clause on page 1. Record each term exactly as written, with its section number. Mark anything not mentioned as "not stated". Never fill a gap with a typical value without saying so.

Term table fields: instrument (preferred shares, in India usually CCPS; SAFE; convertible note), amount, pre-money or post-money valuation and which one it is, option pool size and whether it sits in the pre-money, liquidation preference (multiple, participation, cap, seniority), dividends, anti-dilution (type and carve-outs), pro-rata and super pro-rata, board composition, protective provisions or reserved matters, drag-along (threshold, minimum price, founder consent), tag-along and right of first refusal, founder vesting or re-vesting, information rights, exclusivity (no-shop) length, legal fee cap, conditions to closing, and which clauses are binding.

### 2. Get the inputs the maths needs

The script needs share counts as well as prices. If the founders have not given the fully diluted share count, the existing unallocated pool and the investor's stake, ask for them. If they cannot provide them, use the post-money percentages from the term sheet and say that share counts are illustrative.

### 3. Run the numbers

Run the script instead of doing the arithmetic in your head:

```bash
# Option pool shuffle: price per share, effective pre-money, who pays for the pool
python scripts/term_sheet_math.py pool --pre 20000000 --raise 5000000 --pool-post 0.10 --existing 7000000 --existing-pool 0

# Liquidation preference at low, middle and high exits (use 0.5x, 1x-2x and 5x+ the post-money)
python scripts/term_sheet_math.py waterfall --invested 5000000 --stake 0.20 --multiple 1 --participation none --exits 10000000,25000000,100000000

# Anti-dilution in a hypothetical down round at half the price
python scripts/term_sheet_math.py antidilution --old-price 2.5 --new-price 1.25 --new-money 5000000 --broad 10000000 --narrow 9000000 --invested 5000000
```

- `--pool-post` is the unallocated pool after the round as a fraction of post-money. If the pool is stated as a share of pre-money, convert it first and say so.
- For `--participation`, use `none` (non-participating), `full` (participating) or `cap` with `--cap` (total return multiple).
- Model the down round only when the term sheet has anti-dilution. Present it as "if a later round were priced at half this one", never as a forecast.
- If a script exits with an error, fix the input it names and run it again. Do not estimate instead.

### 4. Rate each clause

Read [references/clauses.md](references/clauses.md) for what founder-friendly, market standard and aggressive look like for each clause, and which questions to ask. Use exactly three ratings: **Founder-friendly**, **Market standard**, **Aggressive**. Base each one on the text, not on the investor's reputation.

Two things change a rating:
- **Stage and leverage.** A 1x non-participating preference is standard at seed and Series A. Stacked or higher multiples are more common in late or distressed rounds. Say which stage you are assuming.
- **Interaction.** A modest clause can bite in combination: participation plus a large preference, a broad veto list plus a board the investors control, or a drag-along with no minimum price.

### 5. Output format

Use this structure:

```markdown
# Term sheet review: [Company], [round], [investor]

## The headline
Two or three sentences: the real price (effective pre-money), what founders own after the round, and the one or two clauses to negotiate first.

## The numbers
| | Headline | Effective |
|---|---|---|
| Pre-money valuation | ... | ... |
| Price per share | ... | ... |
| Founders after the round | ... | ... |
Then the waterfall table and, if relevant, the anti-dilution table, each with one sentence on what it means.

## Clause by clause
| Clause | What it says (section) | Rating | Why |
|---|---|---|---|

## Negotiate first
Up to five asks, most valuable first, each with a fallback position.

## Questions for your lawyer
Numbered, specific to this document.

## Not stated
Terms the document leaves out that usually appear.
```

### 6. Check before sending

- Every number in the review appears in the script output or the term sheet.
- Each rating has a reason that quotes or cites the clause.
- Pre-money and post-money are never mixed up, and the currency matches the document.
- The review ends with: "This is a briefing to discuss with your lawyer, not legal advice."

## Rules

- Quote the document when a clause is ambiguous, and give both readings rather than choosing one silently.
- For Indian rounds, note that the term sheet usually becomes a share subscription agreement (SSA) and a shareholders' agreement (SHA), and that for foreign investors, foreign-exchange pricing rules can limit how far a conversion price can be adjusted.
- Do not tell the founders to accept or reject the term sheet. Show the trade-offs and what to ask for.
