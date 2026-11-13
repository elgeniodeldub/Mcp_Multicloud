---
id: commitment-based-discounts
title: Commitment-based discounts
summary: Buy reservations and savings plans for the stable part of your usage, sized from history after rightsizing, and track coverage and utilization.
domain: Optimize Usage & Cost
capabilities: [Rate Optimization]
phases: [optimize, operate]
providers: [aws, azure, gcp]
related_tools: [finops__get_cost, finops__breakdown, finops__forecast, finops__compare]
tags: [commitment, reservation, reserved instances, savings plans, cud, committed use, coverage, utilization, discount]
---
# Commitment-based discounts

Commitments trade flexibility for a lower rate. The risk is paying for capacity
you no longer use, so commit only to the baseline you are confident in.

## When to use

- Compute or database spend is steady for several months.
- Rightsizing and idle clean-up are done or in progress.
- Coverage is low and finance accepts a 1- or 3-year term.

## Signals

- `finops__breakdown` by `service` shows a stable compute or database baseline.
- Provider recommendations show high estimated savings with high utilization.
- Existing commitments show low utilization (a sign of over-buying).

## Steps

1. Clean first: run the `rightsizing-compute` and
   `idle-and-orphaned-resources` playbooks so the baseline is real.
2. Measure the baseline: call `finops__get_cost` and `finops__breakdown` for the
   last 3-6 months by `service` and `region`. The baseline is the steady
   minimum, not the average.
3. Check the outlook: call `finops__forecast`, and ask owners about migrations,
   decommissions, and architecture changes in the term.
4. Choose the instrument:
   - AWS: Compute Savings Plans (most flexible), EC2 Instance Savings Plans, or
     Reserved Instances (RDS, ElastiCache, OpenSearch, Redshift).
   - Azure: Azure savings plan for compute (flexible) or Reservations (VMs,
     SQL, Cosmos DB, storage, and others).
   - GCP: committed use discounts (resource-based or spend-based); sustained
     use discounts apply automatically to some machine types.
5. Buy in steps: cover part of the baseline (for example half), wait a month,
   check utilization, then buy more. Stagger expiry dates.
6. Track monthly: coverage (share of eligible usage covered) and utilization
   (share of commitment used). Compare `effective_cost` and `billed_cost` in
   `finops__get_cost` to see the amortized effect.
7. Plan renewals 60-90 days before expiry.

## KPIs

- Commitment utilization (target near 100%).
- Commitment coverage of eligible usage (target set with finance).
- Effective savings rate versus on-demand.

## Pitfalls

- Committing before rightsizing locks in waste.
- Reservations tied to a region, family, or OS may not move with workloads.
- Upfront payments distort monthly billed cost; report amortized cost to teams.
- Who benefits (shared versus single account) changes showback results; agree
  the rule first.
- This playbook gives no discount rates; use provider calculators and your own
  agreements for figures.
