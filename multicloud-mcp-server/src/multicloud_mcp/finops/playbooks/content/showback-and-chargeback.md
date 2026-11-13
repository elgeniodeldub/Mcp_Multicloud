---
id: showback-and-chargeback
title: Showback and chargeback
summary: Report each team's cloud cost back to it (showback) and, when the organization is ready, bill it internally (chargeback).
domain: Manage the FinOps Practice
capabilities: [Invoicing & Chargeback, Reporting & Analytics]
phases: [inform, operate]
providers: [aws, azure, gcp]
related_tools: [finops__cost_by_tag, finops__breakdown, finops__get_cost, finops__compare]
tags: [showback, chargeback, internal billing, report, accountability, invoice, cost center]
---
# Showback and chargeback

Showback makes teams see their cost. Chargeback moves the cost into their
budget. Start with showback; chargeback needs trusted allocation first.

## When to use

- Teams do not know what they spend.
- Finance wants cloud cost in departmental budgets.
- Central IT absorbs costs it cannot control.

## Signals

- Cloud cost sits in one central budget line.
- Teams challenge allocation numbers (allocation is not yet trusted).
- The invoice and the internal reports do not reconcile.

## Steps

1. Confirm allocation quality: run `finops__cost_by_tag` for the owner key and
   check the untagged share. Fix allocation before any chargeback.
2. Decide the cost basis with finance: billed cost or amortized
   (`effective_cost`) cost, and how commitments, credits, support, and taxes are
   shared. Write the rules down.
3. Build the monthly report per team: total (`finops__get_cost`), trend
   (`finops__compare`), and top services (`finops__breakdown` by `service`).
4. Reconcile: the sum of all team reports plus unallocated cost must equal the
   provider invoice for the same basis.
5. Run showback for at least two or three cycles. Collect disputes and fix the
   rules.
6. Move to chargeback when disputes are rare and finance agrees on journal
   entries and timing.

## KPIs

- Share of spend shown back to a named owner.
- Number of allocation disputes per cycle.
- Days after month end until reports are delivered.

## Pitfalls

- Chargeback on poor allocation creates conflict, not accountability.
- Changing rules mid-year breaks budget comparisons.
- Accounting treatment (capitalization, tax) is a finance decision; this
  playbook describes mechanics only.
