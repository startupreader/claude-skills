# Conversion rules and the input file

## Contents
- The JSON file, field by field
- How the round is priced
- How each SAFE and note converts
- Which share count a cap divides into
- MFN, interest and maturity
- What to read in the documents
- Indian rounds

## The JSON file, field by field

| Field | Meaning |
|---|---|
| `company`, `currency` | Labels for the output only. |
| `holders` | `[{"name", "shares", "founder"}]`: founders, angels and earlier priced investors with issued shares, and granted options (vested or not), each as its own row. Set `"founder": true` on founders to get their combined stake. |
| `unallocated_pool` | Option pool shares reserved but not yet granted. Default 0. |
| `instruments[].type` | `post-money-safe`, `pre-money-safe` or `note`. |
| `instruments[].amount` | Purchase amount (SAFE) or principal (note). |
| `instruments[].cap` | Valuation cap. Omit or 0 for uncapped. |
| `instruments[].discount` | Discount as a fraction: 0.2 for 20% off the round price. Omit or 0 for none. |
| `instruments[].mfn` | `true` if it has a most-favoured-nation clause. |
| `instruments[].interest_rate` | Notes only: yearly simple interest as a fraction, e.g. 0.08. |
| `instruments[].years` or `issued` | Notes only: years of interest, or the issue date (YYYY-MM-DD) with `round.closing`. `issued` also orders instruments for the MFN check. |
| `instruments[].maturity` | Notes only, optional: flagged if the round closes after it. |
| `instruments[].cap_includes_conversions`, `cap_includes_pool_top_up` | Override the share count the cap divides into (see below). |
| `round.name`, `pre_money`, `raise` | The priced round: headline pre-money and new money. |
| `round.pool_target` | Unallocated pool after the round as a fraction of the fully diluted company, e.g. 0.10. Omit for no top-up. |
| `round.closing` | Closing date, for note interest and maturity. |
| `round.investor_name` | Label for the new investors. Default "<round name> investors". |
| `round.conversions_in_pre_money` | Default `true`. `false` when the term sheet prices the round on today's shares and the pool only. |

The script rejects unknown fields, so a typo fails loudly instead of being ignored.

## How the round is priced

- Price per share = pre-money valuation / pre-money fully diluted shares.
- By default the pre-money share count includes today's holders, granted options, the unallocated pool, the pool top-up and every SAFE and note conversion. The new investors then own exactly raise / post-money, and the pool and conversions are paid for by today's holders. This matches StartupReader's SAFE conversion and dilution calculators, where the round's pre-money includes the SAFE.
- With `conversions_in_pre_money: false` (or `--conversions-outside-pre-money`), conversions are extra shares on top, so they dilute the new investors as well.
- Pool top-up: shares are added before the round until the unallocated pool equals `pool_target` of the fully diluted company after the round. An existing unallocated pool counts toward the target; if it is already above, nothing is added.
- Effective pre-money = round price x today's fully diluted shares. It is what today's holders' stake is priced at once the pool top-up and conversions are taken out of the headline.

## How each SAFE and note converts

Each instrument converts at the lowest of three prices, never more than one of them:
1. Cap price = cap / the share count its document defines (next section).
2. Discount price = round price x (1 - discount).
3. The round price, for an uncapped instrument with no discount or when neither term helps.

Shares = converting amount / that price, rounded down. The converting amount is the purchase amount for a SAFE and principal plus accrued interest for a note.

The price, the pool top-up and the conversions depend on each other, so the script solves them together. Do not try to reproduce the result by hand; rerun the script after any change.

## Which share count a cap divides into

| Type | Default count | Effect |
|---|---|---|
| `post-money-safe` | Today's fully diluted shares plus the shares issued on all SAFE and note conversions; not the round's pool top-up | The holder's stake is fixed at amount / cap of that count. More SAFEs dilute the founders, not this holder. The pool top-up and new money then dilute it like everyone else. |
| `pre-money-safe` | Today's fully diluted shares plus the pool top-up; not the conversions | The stake is not fixed: every further SAFE or note dilutes this holder as well as the founders. |
| `note` | Same as a pre-money SAFE | As for a pre-money SAFE. |

These are the script's defaults. Documents differ, so read the definition of the share count the cap is divided by (often called company capitalisation or fully diluted capitalisation) and set `cap_includes_conversions` and `cap_includes_pool_top_up` to match. State in the answer which count each instrument used.

## MFN, interest and maturity

- MFN (most-favoured-nation): the holder can take better terms the company later gives other investors in similar instruments. The script lists later instruments with a lower cap or a bigger discount but never applies them. If the clause applies, copy the better terms into that instrument, rerun, and show both results.
- Interest: simple interest, principal x rate x years, with years = days from `issued` to `round.closing` / 365. If a note compounds or uses another day count, say that the converting amount is an estimate.
- Maturity: a note has a date by which it should convert or be repaid, and one that reaches it without a plan hands the noteholders leverage. The script flags a closing after maturity; tell the founders to read what the note says happens then.

## What to read in the documents

- SAFE: the purchase amount; whether it is a post-money or pre-money SAFE (the title and the cap definition say); the cap; the discount. Some documents state the price paid instead of the discount: a "discount rate" of 80% means a 20% discount, so enter 0.2. Check for an MFN clause and any side letter, such as pro-rata rights.
- Convertible note: principal, interest rate and whether it compounds, issue date, maturity date and what happens at maturity, cap, discount, and the share count the cap divides into.
- The term sheet: pre-money or post-money valuation, the new money, the pool target and whether it is measured on the post-money company, and whether the pre-money includes the SAFEs and notes.

If a term is missing or ambiguous, ask. Never fill in a typical cap or discount.

## Indian rounds

Indian companies usually raise early money through compulsorily convertible preference shares (CCPS), convertible notes (open to DPIIT-recognised startups under specific rules) or templates such as the iSAFE, which is structured as CCPS. If the instrument's conversion formula works like a cap and discount on the next round's price, model it as the matching type and say so. For foreign investors, foreign-exchange rules generally require the conversion formula to be fixed when the instrument is issued and the conversion price not to fall below the fair value at that time; flag this for the lawyer rather than modelling it.
