---
id: unit-economics
title: Unit economics
summary: Relate cloud cost to a business output, such as cost per customer, transaction, or request, so spend can be judged by value and not only by size.
domain: Quantify Business Value
capabilities: [Unit Economics, Benchmarking]
phases: [inform, operate]
providers: [aws, azure, gcp]
related_tools: [finops__cost_by_tag, finops__get_cost, finops__breakdown, finops__compare]
tags: [unit cost, cost per customer, cost per transaction, kpi, value, margin, business metric]
---
# Unit economics

Total spend going up can be good news if the business grew faster. A unit cost
shows which one happened.

## When to use

- Leadership asks whether cloud spend is "too high".
- Spend grows and nobody can say whether efficiency improved.
- You price a product or feature and need its cost to serve.

## Signals

- Cost reviews discuss totals only.
- No agreed business metric exists for a product.
- Allocation by product is below a reliable level.

## Steps

1. Allocate first: unit cost is only as good as allocation. Run the
   `cost-allocation-tagging` playbook if the product's spend is not allocated.
2. Choose one demand driver per product with its owner (customers, orders,
   API calls, GB processed). It should be measured reliably every period.
3. Get the cost: call `finops__cost_by_tag` with the product key, or
   `finops__get_cost` for the product's accounts, for the same period as the
   business metric.
4. Calculate unit cost = allocated cost / units. Include shared costs by the
   documented split rule, and state whether cost is billed or amortized.
5. Track the trend monthly with `finops__compare`; explain changes with
   `finops__breakdown` by `service`.
6. Set a target unit cost with the product owner and review it with revenue
   per unit, if available.

## KPIs

- Unit cost per product, trend over time.
- Gross margin per unit, where revenue per unit is known.
- Share of spend included in some unit metric.

## Pitfalls

- A metric that is easy to count but unrelated to cost drivers misleads.
- Changing allocation rules breaks the trend; restate history or mark the break.
- Mixing billed and amortized cost between periods creates false changes.
