---
id: cost-allocation-tagging
title: Cost allocation and tagging
summary: Attribute cloud spend to teams, products, and environments with a tag schema, and measure how much spend is still unallocated.
domain: Understand Usage & Cost
capabilities: [Allocation, Data Ingestion]
phases: [inform]
providers: [aws, azure, gcp]
related_tools: [finops__cost_by_tag, finops__breakdown, finops__get_cost]
tags: [tagging, labels, allocation, untagged, ownership, cost center, metadata]
---
# Cost allocation and tagging

Allocation answers "who owns this spend?". Without it, every other FinOps
practice (budgets, showback, unit economics) rests on guesses.

## When to use

- A large share of spend cannot be tied to a team, product, or environment.
- Teams dispute whose resources drive a cost increase.
- You are preparing showback, chargeback, or per-product budgets.

## Signals

- `finops__cost_by_tag` returns a large `(untagged)` bucket for your owner key.
- Tag keys are spelled several ways (`Team`, `team`, `owner`, `Owner`).
- Shared platforms (Kubernetes clusters, networking, logging) have no split rule.

## Steps

1. Agree a minimal schema with finance and engineering. Start with 3-5 keys,
   for example `owner`, `cost-center`, `environment`, `application`. Fix case and
   allowed values in writing.
2. Measure the baseline: call `finops__cost_by_tag` with your owner key for the
   last full month. Record the untagged share.
3. Find where the untagged spend sits: call `finops__breakdown` grouped by
   `service` and `account` to see which services and accounts carry it.
4. Use account or subscription structure as the first allocation layer. An
   account per team or product is easier to enforce than tags on every resource.
5. Enable tags for billing:
   - AWS: activate the keys as cost allocation tags in Billing; only spend after
     activation carries them.
   - Azure: tags on resources flow to Cost Management; use tag inheritance so
     resource-group or subscription tags apply to usage records.
   - GCP: use labels on resources and projects; they appear in billing export.
6. Enforce at creation time, not after: policy (AWS Organizations tag policies
   and SCPs, Azure Policy with `deny` or `modify`, GCP organization policies) plus
   tags in infrastructure-as-code modules.
7. Define split rules for shared costs (even split, proportional to usage, or
   fixed percentages) and document them.
8. Re-run step 2 monthly and track the trend.

## KPIs

- Percentage of spend allocated to an owner (target set with finance; many
  teams aim for 90% or more).
- Number of tag-key variants for the same concept (target: one).
- Time from resource creation to tag compliance.

## Pitfalls

- Tags are not retroactive in AWS billing data after activation; plan for a
  gap in history.
- Some resource types or charges (support, marketplace, some data transfer)
  cannot carry tags; allocate them by rule.
- Large schemas fail. Add keys only when someone uses them in a report.
- Tags are not a security boundary; do not put secrets or personal data in them.
