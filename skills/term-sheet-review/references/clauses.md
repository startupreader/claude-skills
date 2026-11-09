# Term sheet clauses: what to look for

## Contents
- Economics: valuation, option pool, liquidation preference, dividends, anti-dilution, pay-to-play
- Future rounds: pro-rata, right of first refusal, tag-along
- Control: board, protective provisions, drag-along, founder vesting, information rights
- Process: binding terms, exclusivity, costs, closing conditions
- Indian rounds

Ratings describe common practice in seed and Series A rounds. Later or distressed rounds often carry heavier terms; say when that applies.

## Economics

### Valuation (pre-money or post-money)
- Market standard: the term sheet says clearly whether the figure is pre-money or post-money, and what the fully diluted share count includes.
- Aggressive: a "pre-money" that already counts a new or enlarged pool, SAFEs and notes, so the effective price is lower than the headline.
- Ask: "Is the valuation pre- or post-money, and are the new pool and any SAFEs or notes inside it?"

### Option pool
- Founder-friendly: pool sized to a hiring plan for the period until the next round, or created after the round.
- Market standard: pool created or topped up before the investment, inside the pre-money, commonly 10–15% of the post-money company.
- Aggressive: a pool much larger than the hiring plan needs, which lowers the effective pre-money and leaves unused shares that dilute only existing holders.
- Run `pool` to show the effective pre-money. Ask: "Which hires does this pool cover before the next round?"

### Liquidation preference
- Founder-friendly or market standard: 1x non-participating. The investor takes its money back or converts to common, whichever is larger.
- Aggressive: a multiple above 1x, full participation (the investor takes its preference and then its share of the rest), or preferences stacked so later investors are paid ahead of earlier ones in full.
- Middle ground: participation capped at a total return (for example 3x), above which the investor converts.
- Run `waterfall` at a low, middle and high exit. Show what founders and employees receive at the low and middle exits; that is where the terms differ.

### Dividends
- Market standard: non-cumulative, paid only if declared by the board.
- Aggressive: cumulative dividends that accrue each year and are added to the preference.

### Anti-dilution
Anti-dilution lowers the investor's conversion price if shares are later sold below its price, so its preferred shares convert into more common shares. It does not protect against ordinary dilution at a higher price.
- Market standard: broad-based weighted average, with carve-outs for option grants, conversions of existing instruments and approved acquisitions.
- Less favourable: narrow-based weighted average (a smaller A in the formula, so a larger adjustment).
- Aggressive: full ratchet, which drops the conversion price to the new price however few shares are sold. Uncommon in venture rounds; tends to appear when the company has little leverage.
- Ask for carve-outs and a waiver that a set majority of the protected investors can sign. Run `antidilution` to show the extra shares.

### Pay-to-play
Investors keep their protections only if they take up their pro-rata share of a later, usually down, round. Generally helpful to founders because it keeps investors supporting the company.

## Future rounds

### Pro-rata (pre-emptive) rights
- Market standard: the right to buy enough of the next round to keep the investor's percentage, often limited to "major investors" above an agreed holding.
- Check how ownership is measured: fully diluted or issued shares only. Issued-only gives a larger allocation.
- Aggressive: super pro-rata (the right to buy more than its share), especially uncapped or for several rounds. A large pro-rata can crowd out a new lead.

### Right of first refusal (ROFR)
The company and/or investors can buy shares a founder wants to sell, on the same terms. Market standard. Check that small transfers to family trusts or for estate planning are excluded.

### Tag-along (co-sale)
If founders sell, investors can sell the same proportion of their shares on the same terms. Market standard.

## Control

### Board
- Founder-friendly or market standard at seed and Series A: founders keep a majority, or the board is balanced with an independent director both sides agree on.
- Aggressive: investors control the board at an early stage, or appoint the independent director alone.

### Protective provisions (reserved matters)
Decisions that need the investors' consent.
- Market standard: a short, specific list: changing the rights of the investors' shares, issuing senior or equal shares, selling the company, changing the size of the board, large borrowing, winding up.
- Aggressive: everyday decisions such as budgets, hiring and firing executives, contracts above a low limit, or any new share issue including employee options, especially with a separate veto for each investor.

### Drag-along
Holders above a threshold can make everyone else sell on the same terms.
- Founder-friendly: needs founder or common-holder consent, or a minimum price (for example a multiple of the preference).
- Market standard: a majority or supermajority of all holders plus a majority of the preferred.
- Aggressive: the investors alone can drag, with no minimum price, so a sale that pays only the preference can be forced.

### Founder vesting or re-vesting
- Market standard: four years with a one-year cliff, with credit for time already worked if the company is not brand new.
- Aggressive: full re-vesting from zero with no credit, or "bad leaver" terms that take back vested shares for reasons other than misconduct.
- Ask for double-trigger acceleration: shares vest early if the company is sold and the founder then loses their role.

### Information rights
Monthly or quarterly accounts, an annual budget and audit rights. Market standard. Check that the reporting burden is realistic for the team.

## Process

### What binds
Usually binding: exclusivity (no-shop), confidentiality, costs and governing law. Usually non-binding: valuation and almost every other term. Either side can walk away from non-binding terms, most often over a due-diligence problem.

### Exclusivity (no-shop)
- Market standard: 30–60 days.
- Aggressive: longer than 60 days, or no end date. Ask for it to end early if the investor walks away or changes the price.

### Costs
Investors often ask the company to pay their legal fees. Market standard with a cap. Aggressive with no cap or a high one.

### Conditions to closing
Due diligence, final documents, approvals. Note any condition that depends on a third party, such as a regulator or another investor, because it can delay the money.

## Indian rounds
- Investors usually take compulsorily convertible preference shares (CCPS). The term sheet becomes a share subscription agreement (SSA) for the investment and a shareholders' agreement (SHA) for ongoing rights, and the articles of association are amended so those rights can be enforced.
- "Reserved matters" is the usual name for protective provisions.
- For foreign investors, foreign-exchange rules generally require the conversion formula to be fixed when shares are issued and the conversion price not to fall below the fair value at that time, which can limit how far an anti-dilution adjustment can go. Flag this for the lawyer rather than modelling it.
