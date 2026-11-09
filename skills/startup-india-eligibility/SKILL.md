---
name: startup-india-eligibility
description: Checks whether an Indian startup qualifies for DPIIT startup recognition under Startup India and for the benefits that depend on it, namely the Section 80-IAC tax holiday (now Section 140 of the Income-tax Act, 2025), ESOP tax deferral, the Seed Fund Scheme, the Credit Guarantee Scheme and Fund of Funds-backed investment. Works from the entity type, incorporation date, turnover in each financial year, whether it was split from an existing business and what it does. A script tests the age and turnover limits, the 80-IAC incorporation window and the years a tax holiday could cover. Returns an eligibility table, key dates, documents to prepare and official portal links, and covers the angel tax (Section 56) position and what changes with foreign investment. Use when a founder asks about DPIIT recognition, Startup India registration, being a recognised startup, 80-IAC or the startup tax holiday, the IMB certificate, angel tax, ESOP tax, the seed fund scheme, CGSS or other startup benefits in India.
license: MIT
compatibility: Works on claude.ai, Claude Code and the Claude API. The script needs Python 3.8+ (standard library only) and no network access.
metadata:
  author: StartupReader
  version: "1.0"
  homepage: https://startupreader.com/claude-skills/startup-india-eligibility
---

# Startup India eligibility

Turn a company's facts into an eligibility table for DPIIT recognition and the benefits that depend on it, with the dates that matter, the documents to prepare and the official portals. The rules come from [references/rules.md](references/rules.md), last checked on 8 November 2026. Indian rules change in Budgets, so confirm current thresholds on the official portal before relying on them. The answer is a checklist, not tax or legal advice. Say so once, at the end.

## Workflow

Copy this checklist and tick it off as you go:

```
- [ ] 1. Collect the facts
- [ ] 2. Run scripts/eligibility.py
- [ ] 3. Read references/rules.md for what the script does not test
- [ ] 4. Confirm current thresholds on the official portals
- [ ] 5. Write the answer in the output format below
- [ ] 6. Run the self-check
```

### 1. Collect the facts

The entity type and the incorporation date are required. Ask for the rest; if the founder does not know a fact, leave it out and the script marks that test "Needs checking". Never fill a gap with a guess.

| Fact | JSON key | Flag |
|---|---|---|
| Entity type: private-limited, llp, registered-partnership, cooperative-society, one-person-company, public-limited, unregistered-partnership, sole-proprietorship | `entity_type` | `--entity` |
| Incorporation date (certificate of incorporation) | `incorporated` | `--incorporated` |
| Turnover in every financial year since incorporation, April to March | `turnover` | `--turnover FY=AMOUNT` |
| Formed by splitting up or reconstructing an existing business? | `split_or_reconstructed` | `--split` |
| Plant or machinery used before transferred in? | `reused_plant_or_machinery` | `--used-plant` |
| Works on innovation, improvement or a scalable model? | `innovation` | `--innovation` |
| DeepTech? | `deep_tech` | `--deep-tech` |
| Already DPIIT-recognised? Holds the IMB certificate for 80-IAC? | `dpiit_recognised`, `imb_certificate` | `--recognised`, `--imb-certificate` |
| Indian promoters' shareholding, % | `indian_promoters_pct` | `--indian-promoters` |
| Money from other central or state government schemes | `other_government_support` | `--govt-support` |
| Any foreign investors? In default or an NPA? | `foreign_investors`, `in_default` | `--foreign-investors`, `--in-default` |
| Profit of the eligible business by year, actual or projected | `profit` | `--profit FY=AMOUNT` |
| Date to check on (default today) | `as_of` | `--as-of` |

Yes/no facts take yes, no or unknown. Amounts are rupees: `12500000`, `"1.25 crore"` or `"12.5 lakh"`. Ask what the business does in a sentence or two: DPIIT and the IMB judge innovation, so record the founder's answer and treat the test as theirs to confirm. If the founders hold shares through a company abroad, run the checks on the Indian company.

### 2. Run the script

Write the facts to a JSON file shaped like [assets/example-company.json](assets/example-company.json), then run the script instead of working out dates and limits yourself:

```bash
# All checks for the fictional example company
python scripts/eligibility.py assets/example-company.json

# The founder's facts
python scripts/eligibility.py facts.json

# No file: facts as arguments
python scripts/eligibility.py --entity llp --incorporated 2024-06-03 --turnover 2024-25="18 lakh" --turnover 2025-26="1.2 crore" --innovation yes

# What-if: arguments override the file; --only prints one section (dpiit, 80iac, seed-fund, cgss, dates)
python scripts/eligibility.py facts.json --only 80iac --turnover 2029-30=1040000000
```

- Every line is Eligible, Not eligible or Needs checking. "(as stated)" means the line repeats the founder's answer.
- The 80-IAC section lists the ten-year window and each three-year block still open, with the profit it would cover from the figures given. Projected turnover over ₹100 crore drops that year from a block. Blocks that began in past years are summarised in one line for a chartered accountant (CA) to look at.
- If the script exits with `Error: ...`, fix the input it names and run it again. Do not estimate instead.

### 3. Rules the script does not test

Read [references/rules.md](references/rules.md) before writing. It covers angel tax, the ESOP deferral, Fund of Funds, foreign investment, Udyam registration, the documents for each application and the official portals. Keep these straight:

- **Recognition is not the tax holiday.** 80-IAC needs a separate certificate from the Inter-Ministerial Board (IMB), with stricter tests: company or LLP only, incorporated from 1 April 2016 and before 1 April 2030, turnover under ₹100 crore, no DeepTech extension.
- **ESOP deferral follows the IMB certificate**, not recognition alone. Do not state the deferral period for shares allotted from 1 April 2026; rules.md explains why.
- **Name the section once:** "Section 80-IAC (now Section 140 of the Income-tax Act, 2025)", then 80-IAC.
- **Angel tax** stopped applying from 1 April 2025, but valuations are still needed for foreign investors and preferential allotments. For shares issued during 2024-25, send the founder to a tax adviser.
- **Never round or merge limits.** Recognition is "below ₹200 crore in every financial year"; 80-IAC is "under ₹100 crore". Keep "in every financial year".
- **Recognition is free** and DPIIT appoints no agents. Never suggest paying one.

### 4. Confirm current thresholds

rules.md was last checked on 8 November 2026. Union Budgets (usually in February) and notifications change these rules.

- If you can browse, open the official page listed in rules.md for each benefit in your answer and compare the figures. If one differs, use the official figure and say what changed.
- If you cannot browse, say that the figures were last checked on 8 November 2026 and should be confirmed on the portal.
- If today is after a Union Budget later than 8 November 2026, say that the Budget may have changed these rules.

### 5. Output format

```markdown
# Startup India eligibility: [Company]
Checked on [date], using rules last verified on 8 November 2026.

## Eligibility
| Benefit | Status | Rule | Fact it depends on |
|---|---|---|---|
| DPIIT recognition | ... | ... | ... |
| Section 80-IAC tax holiday | ... | ... | ... |
| ESOP tax deferral | ... | ... | ... |
| Angel tax | ... | ... | ... |
| Seed Fund Scheme | ... | ... | ... |
| Credit Guarantee Scheme | ... | ... | ... |
| Fund of Funds (through AIFs) | ... | ... | ... |
| Foreign investment | ... | ... | ... |  (only if there are or will be foreign investors)
Then one sentence for each "Needs checking" row on what would settle it.

## Dates that matter
Earliest first: deadlines already passed (marked), the three-year tax holiday blocks still open with the profit each covers, the end of the 80-IAC window, the end of recognition, and any year in which projected turnover crosses a limit.

## Documents to prepare
Grouped by benefit, only for benefits that are Eligible or Needs checking.

## Official portals
The links from references/rules.md for the benefits above.

This is a checklist to discuss with your chartered accountant or lawyer, not tax or legal advice. The rules were last checked on 8 November 2026; confirm current thresholds on the official portals.
```

Use the three statuses exactly for benefits. The angel tax and foreign investment rows are not benefits: say what applies instead. Write rupees as ₹ with lakh and crore, and financial years as FY 2025-26.

### 6. Self-check

- Every date, amount and percentage comes from the script output, the founder's facts or references/rules.md.
- Each row gives the rule and the fact it turns on.
- Recognition and the tax holiday are separate rows, and the ESOP row depends on the IMB certificate.
- Holiday blocks say "could cover", never "will save". You show the blocks; a CA confirms the choice, because real tax depends on more than profit.
- Step 4 was done, and the answer says how.
- The answer ends with the disclaimer above.
