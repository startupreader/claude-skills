# Slide checklist: what each slide must show

## Contents
- How to rate
- Stage expectations
- The twelve sections: problem, solution, why now, market, product, traction, business model, competition, go-to-market, team, financials, the ask and use of funds
- Words to flag

## How to rate

Rate each slide against the section it covers, with one of:

- **Strong**: shows everything in "Must show" for its section, with evidence, and agrees with the rest of the deck.
- **Needs work**: the right content, but a number lacks a definition, period, date or source, or the point is buried.
- **Weak**: the core element is absent, a claim has no support, or a number contradicts another slide.
- **Missing**: no slide covers the section. Say whether the stage makes it essential.

Rate what is on the slide, not how good the business is. A slow-growing company with an honest, well-defined traction slide rates Strong on that slide.

## Stage expectations

From StartupReader's funding stage explainers. Labels vary between investors and countries, so if the deck does not state its stage, infer it from the ask and the traction and say so.

| Stage | What the round pays for | What investors look for | What the deck needs most |
|---|---|---|---|
| Pre-seed | Turning an idea into a first product | The founders, the problem, early signs of demand | Why this team, how painful the problem is, any evidence of demand (waitlist, design partners, pilot customers, engagement with a prototype), and what the money will prove and by when |
| Seed | Finding product-market fit | Users or revenue growing without heavy pushing | Defined traction with periods, retention or repeat use, early unit economics |
| Series A | Building a repeatable way to grow | A working sales or growth engine and solid unit economics | Channel-level acquisition cost, LTV:CAC and payback, cohorts, a plan that shows what more money does to growth |

At pre-seed, a clear plan for what the money will prove matters more than a detailed five-year forecast. Do not mark a pre-seed deck down for thin financials; do mark it down for an unclear ask or no evidence of demand.

## The twelve sections

### 1. Problem
- Must show: a specific customer (not "everyone" or "businesses"), what the problem costs them in money, time or risk, how often it happens, and how they deal with it today.
- Weak if: the problem is stated as the absence of the product ("there is no app for X"); no evidence beyond the founders' view, such as interviews, data or a customer quote.
- Investors ask: How do they solve it today, and what does that cost them? How many people have you spoken to who have this problem?

### 2. Solution
- Must show: what the product does for that customer, in one sentence, and the outcome compared with today's alternative.
- Weak if: a list of features with no outcome; jargon that a generalist investor would not follow.
- Investors ask: Why will customers switch from what they do today?

### 3. Why now
- Must show: what changed (technology, regulation, cost, behaviour, distribution) that makes this possible or necessary now and not five years ago.
- Weak if: only "the market is growing" or a market growth rate with no change behind it.
- Investors ask: What stops an incumbent doing this now that it is possible?

### 4. Market
- Must show: a bottom-up build. Customer segments, a count of customers in each with its source, the price each would pay a year, and which part the product and channels can reach today. TAM, SAM and SOM labelled correctly:
  - TAM: the whole demand for the product category (every customer in every segment, times price).
  - SAM: the part the company's product and channels can serve.
  - SOM: the share it can realistically win in the near term.
- Weak if: only a top-down figure (an industry report total, or "1% of a huge market"); no source or year; TAM labelled as SAM; a SOM the revenue plan does not fit inside. Investors trust bottom-up estimates more than top-down ones.
- Run `market` in scripts/market_size.py with the deck's own counts and prices. If the deck gives no counts, do not supply your own: list the rebuild as a fix and ask the founders for the counts.
- Investors ask: Where does the customer count come from? Who pays, and how much a year? Why that share of SAM?

### 5. Product
- Must show: what it looks like and how it works (screenshots or a demo link), what is live today and what is still planned.
- Weak if: mock-ups presented as a live product without saying so; a roadmap with no timing or no link to the raise.
- Investors ask: What is built, what is next, and what does this round pay to build?

### 6. Traction
- Must show: each metric defined, with the period and an as-of date. Growth shown with start and end values. Retention or repeat use where the stage allows.
- Definitions to check:
  - Users: signed up, active (in what window) or paying.
  - Revenue: recognised revenue, GMV, bookings, or recurring revenue. MRR and ARR count only recurring fees from active customers; one-off setup and services fees and unpaid pilots are excluded.
  - ARR: run-rate ARR (current MRR x 12) or contracted ARR (signed recurring contracts, including some not yet live). "Revenue run-rate" built from one month's total revenue x 12, including one-off fees or a seasonal peak, is not ARR.
  - Customers and logos: paying customers, paid pilots, unpaid pilots or letters of intent. Logos on a slide should say which.
- Weak if: a cumulative chart with no label (a cumulative total can only rise); sign-ups or downloads with no activity measure; a growth rate with no period; "40% growth" without saying month on month, year on year or best month.
- Run `growth` with the deck's own first and last data points to check any stated growth rate.
- Investors ask: What does an active user mean here? How many of these customers pay, and how many renewed?

### 7. Business model
- Must show: who pays, how much and how often; gross margin if known. From seed onward, unit economics with their definitions:
  - CAC: all sales and marketing spend (including salaries, tools and agencies) divided by new customers won in the same period.
  - LTV: average monthly revenue per customer x gross margin / monthly churn rate. It uses gross profit, not revenue.
  - CAC payback: CAC / (monthly revenue per customer x gross margin).
  - A common rule of thumb for subscription businesses is LTV:CAC of at least 3:1 and payback within about 12 to 18 months. Treat these as guides, not pass marks: early cohorts are small and churn estimates are noisy.
  - For marketplaces, consumer brands and delivery businesses, contribution margin per order (after product cost, payment fees, delivery, discounts and returns) often matters more.
- Weak if: price not stated; LTV built on revenue; churn extrapolated from a few months as if customers stay for years; one blended CAC hiding channels.
- Investors ask: What does it cost to win a customer, by channel, and how long until they pay it back?

### 8. Competition
- Must show: the alternatives customers use today, including spreadsheets, manual work, an in-house build or doing nothing; how the company compares on what customers care about; why it wins and how it keeps winning.
- Weak if: "no competitors" or "no direct competition"; a two-by-two chart with axes chosen so only the company sits in the best corner; an obvious alternative left out.
- Investors ask: Who do you lose deals to, and why?

### 9. Go-to-market
- Must show: how the company reaches its first and next customers (channels, sales motion, sales cycle), what that costs, and evidence that at least one channel works.
- Weak if: channels listed with no evidence or cost ("viral", "partnerships", "social media"); the plan cannot produce the number of customers the financials need. The `market` run with `--revenue-target` gives that number.
- Investors ask: Which channel brought your last ten customers? What will the next 100 cost?

### 10. Team
- Must show: who does what, who is full-time, and why this team is suited to this problem (relevant experience, customer access, technical depth). Key hires the round pays for.
- Weak if: advisers outnumber the team; roles unclear; a gap the plan depends on (for example, nobody who has sold to this customer) is not addressed.
- Investors ask: Why are you the people to build this? Who do you hire first with this money?

### 11. Financials
- Must show: historical figures kept apart from projections; the assumptions behind the projections (customers, price, churn, hiring); burn and runway.
- Weak if: a revenue curve with no assumptions; projected revenue larger than the SOM; customer numbers the go-to-market plan cannot reach; a growth rate that does not match the traction slide; a break-even date that contradicts the burn plan.
- At pre-seed, a short plan for what the money proves is enough.
- Investors ask: Which assumption, if wrong, changes the plan most?

### 12. The ask and use of funds
- Must show: the amount, the instrument (priced equity, SAFE, convertible note; in India usually CCPS for priced rounds, or CCDs or convertible notes), the valuation or cap if the founders choose to state it, how long the money lasts, the milestone it reaches, and a use of funds that adds up to the raise.
- Checks, using `runway` in scripts/market_size.py:
  - Runway from the raise plus cash in the bank and the planned net burn. Rounds are usually sized to last 18 to 24 months, because a raise itself can take three to six months; the next round should be in preparation with about a year of runway left.
  - Any runway the deck claims, against the burn plan.
  - Use of funds adds up to the raise (percentages to 100%).
  - For a priced round with a stated pre-money, the stake sold. Priced rounds commonly sell 10% to 25% of the company; pre-seed rounds often sell 10% to 20% in total.
- Weak if: no amount; no milestone; use of funds does not add up; claimed runway does not match the burn plan.
- Investors ask: What will be true when this money runs out that makes the next round possible?

## Words to flag

Flag these when the deck gives no number or source to back them: first, only, leading, largest, best, unique, revolutionary, disruptive, world-class, unmatched, guaranteed, massive, huge, explosive, no competition, no competitors. Quote the phrase, give the slide, and suggest the evidence that would replace it (a metric, a customer quote, a source). Do not flag the same word when it is backed: "the only supplier certified for X (certificate on slide 14)" is fine.
