# SaaS metric definitions and rules of thumb

## Contents
- Preparing the data: what counts as MRR
- Monthly classification
- Formulas the script uses
- Conventions that differ elsewhere
- Rules of thumb (and how to quote them)
- Mistakes that flatter the numbers

## Preparing the data: what counts as MRR

MRR is recurring subscription revenue normalised to one month, after discounts. Build one row per customer per month before running the script.

- Annual plan: divide by 12 and count it in every month it covers, not in the month it is invoiced. Quarterly: divide by 3.
- Include subscription and licence fees on active contracts and recurring add-ons (extra seats, modules).
- Exclude one-time setup, implementation and onboarding fees; consulting and custom work; hardware; free trials and unpaid pilots; VAT, GST and sales tax.
- Usage-based fees: many companies count a committed minimum and report variable usage separately. Pick one treatment and say which.
- One currency per file. Convert at a stated rate before running.
- A customer who changes ID (merger, new billing account, renamed workspace) shows up as one churn and one new customer. Merge the IDs first if the founder confirms it is the same customer.
- Revenue and ARR are different: revenue is what was recognised over a period, including one-off income; ARR is a run rate at a point in time.

## Monthly classification

For each customer, this month's MRR is compared with last month's:

| Last month | This month | Movement |
|---|---|---|
| 0, never paid before | > 0 | New |
| 0, paid in an earlier month | > 0 | Reactivation |
| > 0 | 0 | Churned (all of last month's MRR) |
| > 0 | higher | Expansion (the increase) |
| > 0 | lower, above 0 | Contraction (the decrease) |

A customer who churned before the file starts and comes back inside it is counted as new, because the file has no earlier history. The first month in the file is the opening balance: it has no movements.

## Formulas the script uses

These match StartupReader's calculators and explainers (ARR and MRR, churn rate, LTV and CAC, burn rate and runway; arr-vs-mrr, unit-economics-ltv-cac, burn-multiple, rule-of-40).

- Net new MRR = new + reactivation + expansion - contraction - churned. The site's bridge has four parts (new, expansion, contraction, churned); reactivation is shown on its own line so returning customers are not mistaken for new ones. Add it to new to get the four-part version.
- MRR growth = net new MRR / starting MRR.
- ARR = ending MRR x 12 (run-rate ARR). Contracted ARR, which adds signed contracts not yet live, is a different number.
- Logo (customer) churn = customers lost / customers at the start of the month. Customers who joined during the month are not in the denominator.
- Annual churn, compounded = 1 - (1 - monthly churn)^12. 2% a month is about 21.5% a year, not 24%.
- Gross revenue churn = (contraction + churned MRR) / starting MRR.
- Net revenue retention (NRR) = (starting MRR + expansion - contraction - churned) / starting MRR. New and reactivated customers are excluded.
- Gross revenue retention (GRR) = (starting MRR - contraction - churned) / starting MRR = 100% - gross revenue churn. It cannot exceed 100%.
- Cohort NRR over a period = what customers paying in the base month pay now / what they paid then. With 13 months of data this is the 12-month NRR investors usually quote. Cohort GRR caps each customer at their base-month MRR.
- ARPA (average revenue per account) = ending MRR / customers at the end of the month.
- CAC = sales and marketing spend / new customers won in the same period.
- LTV = ARPA x gross margin / monthly churn. The script uses the average monthly logo churn over the window unless `--churn` is given.
- LTV:CAC = LTV / CAC.
- CAC payback (months) = CAC / (ARPA x gross margin).
- Net burn = monthly expenses - monthly revenue (the cash lost, leaving out money raised).
- Runway (months) = cash / net burn, with burn held flat. StartupReader's burn rate and runway calculator also models revenue and cost growth.
- Burn multiple = net burn / net new ARR over the same period. The script uses the last 3 months: (net burn x 3) / ((ending MRR now - ending MRR 3 months ago) x 12).
- Rule of 40 score = revenue or ARR growth over 12 months (%) + profit margin (%), with EBITDA or free cash flow margin. 40 or more passes.

## Conventions that differ elsewhere

Billing tools and dashboards make different choices. When the founder's own numbers disagree with the script, check these before assuming an error, and label which convention each figure uses.

- Churn on average customers ((start + end) / 2) instead of starting customers: gives a lower rate in a growing company. The site uses starting customers.
- Gross revenue churn without contraction (cancellations only): the site counts downgrades too.
- Reactivations folded into new MRR, or netted against churn.
- NRR over 12 months on a cohort, or a single month's NRR: say which. A monthly NRR of 99% is not the same as a 12-month NRR of 99%.
- LTV on revenue instead of gross profit: overstates LTV. The site uses gross profit.
- ARPA on average customers or on customers at the start.

## Rules of thumb (and how to quote them)

Quote these as rules of thumb, never as standards, and only these. They come from StartupReader's explainers and calculators. Do not add percentile benchmarks or attribute figures to named firms.

- LTV:CAC: at least 3:1 is the common rule of thumb for subscription businesses. Below 1:1, each customer loses money. Well above 5:1 can mean the company could invest more in growth.
- CAC payback: within about 12 to 18 months is the common aim. Often under 12 months for small-business software and up to 18 to 24 months for enterprise contracts with low churn.
- NRR: above 100% means existing customers grow on their own, before any new sales. What is strong varies a lot by market and customer size.
- Churn: there is no single good rate. Companies selling to small businesses usually see higher monthly churn than those selling to large enterprises on annual contracts. Compare with similar products and customers.
- Burn multiple: the bands most often quoted come from a framework popularised by investor David Sacks in 2020: under 1x amazing, 1x to 1.5x great, 1.5x to 2x good, 2x to 3x suspect, over 3x bad. Earlier-stage companies usually run higher multiples, and on a small ARR base one deal can swing it. Use a quarter or 12 months, not one month.
- Runway: raising usually takes three to six months, so founders aim to start a round with at least 9 to 12 months of runway and to raise enough for 18 to 24 months. Under 6 months, the company negotiates from weakness.
- Rule of 40: meant for scaled software companies. At seed and Series A, growth from a small base swings too much for the score to mean much; retention and burn multiple are better guides.

## Mistakes that flatter the numbers

- Booking an annual plan as MRR in the month it is paid.
- Counting trials, setup fees or services as recurring revenue.
- Using revenue instead of gross profit in LTV.
- Leaving salaries, tools and agency fees out of sales and marketing spend.
- Extrapolating churn from a few good months: early customers are often the keenest.
- Reporting only net new MRR, which hides rising churn behind strong new sales.
- Blending everything into one average. Compare cohorts (customers grouped by the month they started): if newer cohorts churn faster, the average hides it.
