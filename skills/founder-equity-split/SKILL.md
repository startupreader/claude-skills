---
name: founder-equity-split
description: Works out a starting point for splitting equity between co-founders with a weighted-factor scorecard (full-time commitment, idea and early work, domain expertise, building the product, sales and fundraising, money put in, each scored 0 to 10), then models founder vesting over four years with a one-year cliff and credit for time already worked, what a co-founder who leaves keeps, and how funding rounds and an option pool dilute every founder alike. Finishes with the terms to settle in a founders' agreement. Use when founders ask how to split equity or shares between co-founders, whether 50/50 is fair, how much a part-time or late co-founder should get, how founder vesting, reverse vesting or a cliff works, what happens if a co-founder leaves, what dead equity is, how dilution will affect each founder, or what goes in a founders' or co-founder agreement.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/founder-equity-split
---

# Founder equity split

Help co-founders agree a split, protect it with vesting, see what leaving and funding would do to it, and list what to write down. The scorecard gives a starting point for the conversation, not a verdict: the founders decide. All arithmetic comes from the script. End with one line saying this is not legal or tax advice.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Gather each founder's role, commitment, start date and money put in
- [ ] 2. Propose scores with a reason each, and let the founders change them
- [ ] 3. Run the split, plus a re-run on the most disputed factor
- [ ] 4. Model vesting and a founder leaving
- [ ] 5. Model funding rounds and the option pool, if they plan to raise
- [ ] 6. List the founders' agreement terms (references/founders-agreement.md)
- [ ] 7. Write the answer in the output format and check every figure
```

### 1. Gather the facts

For each founder: what they will do from now on, full time or part time (and until when), when they started working on the company, and any money put in. Also the total founder shares; if none are issued yet, use 10,000,000 and say it is illustrative.

### 2. Score the founders

The scorecard has six factors with fixed weights. Do not add, drop or reweight factors: the method is StartupReader's equity split calculator, and founders can check the result there.

| Factor | Weight | What to score, 0 to 10 |
|---|---|---|
| Full-time commitment | x3 | Time each founder will give from now. 10 for full time; lower for part time or a later start (for example 4 for keeping a day job for the first year). |
| Idea and early work | x1 | The idea, prototype and work done so far. |
| Domain expertise | x2 | Knowledge of the industry and customers the company needs. |
| Building the product | x2 | Who will build it. |
| Sales and fundraising | x2 | Who will sell it and raise money. |
| Money put in | x1 | Cash contributed. Equal small amounts can score the same for everyone. A larger or unequal amount is better treated as a loan or an investment on the same terms as outside investors; then score everyone 0 so it does not count twice. |

Score the future more than the past: equity mainly rewards the years of work ahead. Give one reason per score and ask the founders to confirm or change them before running anything.

### 3. Run the split

```bash
python scripts/equity_split.py split --founder Riley:10,8,6,9,4,5 --founder Morgan:10,4,8,3,9,5
```

Scores go in factor order: commitment, idea, expertise, building, sales, money. Re-run with the most disputed score changed to show how much it moves the split. Typically the idea barely moves it, while commitment moves it a lot.

The result is a starting point. Equal or near-equal splits are common between full-time founders who start together; a large gap should reflect future roles, such as a part-time or much later co-founder, not who had the idea. Record the split the founders agree, even if it differs from the script's.

### 4. Model vesting and a leaver

```bash
# One founder's schedule, with 6 months' credit for time already worked
python scripts/equity_split.py vesting --shares 5000000 --credit 6 --at 18

# What a founder leaving at 18 months keeps, and the split afterwards
python scripts/equity_split.py leave --founder Riley:5000000 --founder Morgan:5000000 --leaver Morgan --months 18
```

The defaults are four years, a one-year cliff and monthly vesting after it (`--total 48 --cliff 12`). Show a leaver just before the cliff and one or two dates after it. If the company already has investors or a pool, pass their shares with `--others` so the percentages cover the whole company.

### 5. Model funding

```bash
python scripts/equity_split.py dilute --founder Riley:5000000 --founder Morgan:5000000 \
  --round "Pre-seed:500000:2000000" --round "Seed:2000000:8000000:0.10" --round "Series A:10000000:40000000:0.12"
```

A round is `NAME:RAISE:PRE-MONEY[:POOL]`, with POOL the option pool after the round as a fraction of post-money, created before the investment. Use the founders' own plan; if they have none, say the rounds are illustrative. The script shows that every round and pool top-up scales all founders by the same factor, and what the pool costs them. For SAFEs, notes and an exact priced round, suggest the cap-table-modeling skill.

### 6. List the agreement terms

Read [references/founders-agreement.md](references/founders-agreement.md) and fill each term in with this team's numbers. It is a term list to take to a lawyer, not a draft.

### 7. Output format

```markdown
# Founder equity: [Company]

## Suggested split
The scorecard from the script (factors, weights, scores, points, split) and one sentence on what drove it.

## What would change it
One line per re-run: the changed score and the new split.

## Vesting
| Founder | Shares | Credit | Cliff reached | Fully vested |
|---|---|---|---|---|

## If a founder leaves
| Leaves after | Keeps | Back to the company | Split afterwards |
|---|---|---|---|

## After funding
The founders' stakes after each round, the pool's cost, and the paper value after the last round.

## Founders' agreement: terms to settle
The eight terms, filled in with this team's numbers and open questions.

This is a starting point for your conversation and a brief for your lawyer, not legal or tax advice.
```

Check before sending:
- Every percentage and share count appears in the script output. Nothing is recomputed by hand.
- The scores in the answer match the ones the founders confirmed.
- The split is presented as a starting point, and the agreed split, if different, is stated separately.
- Vesting dates say whether they count from signing or include credit for time already worked.

## Rules

- Stay neutral between founders. Never argue one founder's case; explain what each score does.
- Use they/them for founders unless the user says otherwise.
- Founders already own their shares, so founder vesting is reverse vesting: the company can take back or buy back the unvested part. Once there are investors it usually sits in the shareholders' agreement, in India as elsewhere. Leave the drafting to the lawyer.
