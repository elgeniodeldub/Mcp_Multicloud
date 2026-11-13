---
id: budgeting-and-forecasting
title: Budgeting and forecasting
summary: Set budgets per owner, forecast spend to period end, and act on variance before the invoice arrives.
domain: Quantify Business Value
capabilities: [Budgeting, Forecasting, Planning & Estimating]
phases: [inform, operate]
providers: [aws, azure, gcp]
related_tools: [finops__budgets, finops__forecast, finops__get_cost, finops__compare]
tags: [budget, forecast, variance, plan, overspend, alert, month end]
---
# Budgeting and forecasting

A budget is a commitment from an owner. A forecast says whether that commitment
will hold. Both matter only if someone acts on the variance.

## When to use

- Finance asks for next quarter's cloud forecast.
- Teams find out they overspent after the invoice.
- Budgets exist but are not tied to owners.

## Signals

- `finops__budgets` shows `forecast_pct` above 100% or `alert: true`.
- `finops__forecast` for the current month exceeds the agreed budget.
- No budget exists for accounts or subscriptions that carry large spend.

## Steps

1. Get the baseline: call `finops__get_cost` for the last three full months and
   `finops__compare` between them to see the trend.
2. Forecast: call `finops__forecast` to the end of the month or quarter. Treat
   the provider's interval as uncertainty, not a guarantee.
3. Add known changes the model cannot see: launches, migrations, commitment
   purchases, price changes, decommissions.
4. Set budgets per owner (account, subscription, or tag) with alert thresholds
   on actual and forecast spend (for example 80% actual, 100% forecast).
   - AWS: AWS Budgets.
   - Azure: Cost Management budgets at subscription or resource-group scope.
   - GCP: Cloud Billing budgets per project or label.
5. Review: call `finops__budgets` weekly. For each alert, the owner explains the
   variance and chooses: reduce, accept and re-forecast, or request more budget.
6. Measure forecast accuracy each period and adjust the method.

## KPIs

- Forecast accuracy: absolute variance between forecast and actual, as a
  percentage of actual.
- Share of spend covered by an owned budget.
- Number of budget overruns found after month end (target: zero).

## Pitfalls

- Provider forecasts extrapolate history; they miss planned changes.
- Annual or upfront commitment charges distort monthly views; decide whether
  budgets use billed or amortized cost and keep it consistent.
- Budgets in a different currency from billing create false variances.
- A budget alert to a shared mailbox is rarely acted on.
