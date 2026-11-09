---
name: pitch-deck-review
description: Reviews a startup's investor pitch deck slide by slide against the standard structure (problem, solution, why now, market, product, traction, business model, competition, go-to-market, team, financials, the ask and use of funds). Rebuilds TAM, SAM and SOM bottom-up from customer counts and prices, checks that numbers agree across slides, that traction claims say what they measure and over what period, that the runway claim matches the burn plan and that the deck fits its stage, and flags unsupported superlatives. Returns a scorecard per slide, the five fixes that matter most, missing slides and the questions investors will ask. Use when a founder shares a pitch deck, investor deck, fundraising deck or slides (PDF, PPTX or images), or asks for deck feedback, a market size or TAM/SAM/SOM check, a traction slide review, use of funds, runway, or whether a deck is ready before a pre-seed, seed or Series A raise.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/pitch-deck-review
---

# Pitch deck review

Read the deck the way an investor would on a first pass, then show the founders exactly what to fix. Judge substance, not design: mention layout only where it hides a number or a point.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Map every slide to the twelve sections; note stage, amount and instrument
- [ ] 2. Build the number ledger and find conflicts
- [ ] 3. Run the checks with scripts/market_size.py
- [ ] 4. Rate every slide using references/slide-checklist.md
- [ ] 5. Write the review in the output format below
- [ ] 6. Check every figure against the deck and the script output
```

### 1. Map the deck

Read every slide before judging any, including the appendix and speaker notes. Text inside charts, tables and screenshots counts. If a file cannot be read, ask for a PDF export rather than guessing.

Map each slide to one of the twelve sections: problem, solution, why now, market, product, traction, business model, competition, go-to-market, team, financials, the ask and use of funds. A slide can cover two sections and a section can span several slides. Sections with no slide are **Missing**.

Record: company, stage (pre-seed, seed, Series A; if not stated, infer it from the ask and the traction and say so), amount, instrument, and any valuation or cap the deck states.

### 2. Build the number ledger

List every figure: value, slide, what it measures, period or as-of date, and source. Then look for:

- **Conflicts**: the same metric with different values on different slides (summary versus traction, ask versus use of funds).
- **Undefined metrics**: users (signed up, active or paying?), revenue (recognised, GMV, bookings or recurring?), ARR (run-rate or contracted, or one month's total revenue x 12?), customers (paying, pilots or letters of intent?). Mark each as "not defined" rather than assuming.
- **Missing periods**: a total or a growth rate with no time window or date.
- **Cross-slide links**: price x customers against stated revenue, projected revenue against the SOM, the number of customers the plan needs against the go-to-market plan, the claimed runway against the burn plan.

### 3. Run the checks

Run the script instead of doing the arithmetic in your head:

```bash
# Bottom-up market: one --segment per customer group: NAME CUSTOMERS PRICE_PER_YEAR [SERVICEABLE_SHARE]
python scripts/market_size.py market --segment "Independent clinics" 40000 1200 50% --segment "Group practices" 6000 4800 25% --som-share 3% --claimed-tam 4200000000 --revenue-target 2400000

# Runway and use of funds: net burn by phase as AMOUNT:MONTHS, last phase open-ended
python scripts/market_size.py runway --raise 1500000 --cash 100000 --burn 60000:6,85000 --claimed-months 24 --pre-money 6000000 --use "Product and engineering" 45% --use "Sales and marketing" 35% --use "Operations" 20%

# A growth claim, from the deck's own first and last data points
python scripts/market_size.py growth --start 8000 --end 30000 --periods 9 --per month --claimed-rate 40%
```

- **Market**: counts, prices and shares come from the deck or the founders, never from you. If the deck quotes only a top-down figure, ask for customer counts and prices; if there are none, make the bottom-up rebuild a top fix instead of inventing counts. Use `--monthly` when prices are monthly. `SERVICEABLE_SHARE` is the part of a segment the product and channels reach today (language, geography, product fit, channel). Pass the deck's own TAM, SAM or SOM with `--claimed-tam`, `--claimed-sam`, `--claimed-som`, and the revenue in the last year of its plan with `--revenue-target`.
- **Runway**: `--burn` is planned net burn (spending minus revenue) after the round. Use phases when the plan hires: `60000:6,85000` means 60,000 a month for six months, then 85,000. `--cash` is cash in the bank only, not money promised. Pass `--pre-money` only for a priced round with a stated pre-money.
- **Growth**: `--periods` counts intervals between the two data points (January to October is 9 months). Use it for every stated growth rate.
- For any other sum, such as price x customers, run a one-line `python -c "print(...)"` rather than estimating.
- If a script exits with an error, fix the input it names and run it again.

### 4. Rate each slide

Read [references/slide-checklist.md](references/slide-checklist.md) for what each section must show, what makes it weak, the stage expectations and the words to flag. Use exactly four ratings: **Strong**, **Needs work**, **Weak**, **Missing**.

Two things change a rating:
- **Stage.** A pre-seed deck with thin financials can still be Strong; one with no evidence of demand or no clear ask cannot. A Series A deck without unit economics is Weak on business model.
- **Consistency.** A slide that is fine alone becomes Weak if it contradicts another, for example a revenue plan larger than the SOM or a runway claim the burn plan does not support.

### 5. Output format

```markdown
# Pitch deck review: [Company], [stage], raising [amount]

## The verdict
Two or three sentences: what the deck does well, the biggest problem, and whether it fits the stage.

## Scorecard
| # | Slide | Section | Rating | What works | What to fix |
|---|---|---|---|---|---|

## Five fixes that matter most
Numbered, most important first. Each: the slide, the fix, and why an investor cares.

## Numbers that don't agree
| Figure | Slide | Conflicts with | What the check shows |
|---|---|---|---|

## Missing slides
Each missing section, and whether this stage needs it.

## Words to back up or cut
Quoted phrase, slide, and the evidence that would replace it.

## Questions investors will ask
Numbered, specific to this deck, each with the slide that prompts it.
```

Keep the five fixes to five even when there are more problems; put the rest in the scorecard.

### 6. Check before sending

- Every figure in the review appears in the deck or in the script output.
- Every Weak or Missing rating says what is absent.
- No market sizes, competitor names, benchmarks or statistics that are not in the deck or in references/slide-checklist.md.
- Fixes say what to show, not just "add more detail".

## Rules

- Review the deck, not the founders' chances: never predict whether the round will close or name investors to approach.
- Do not add facts about the market or competitors from memory. Ask for the source instead.
- Quote the deck when flagging a claim, with its slide number.
- Do not rewrite the whole deck unless asked. A sample headline for a weak slide is fine.
