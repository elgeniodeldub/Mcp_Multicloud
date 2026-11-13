---
id: rightsizing-compute
title: Rightsizing compute
summary: Match virtual machine, container, and database sizes to measured demand, starting with the largest and least utilized resources.
domain: Optimize Usage & Cost
capabilities: [Workload Optimization]
phases: [optimize]
providers: [aws, azure, gcp]
related_tools: [multicloud__discover_resources, finops__breakdown, finops__get_cost, multicloud__map_resource]
tags: [rightsizing, rightsize, underutilized, oversized, cpu, memory, vm, instance, ec2]
---
# Rightsizing compute

Rightsizing lowers usage, not rates. Do it before buying commitments, so you do
not commit to capacity you will remove.

## When to use

- Compute is one of the largest services in your bill.
- Instances were sized at launch and never reviewed.
- You plan a commitment purchase in the next quarter.

## Signals

- `finops__breakdown` by `service` shows compute and databases near the top.
- Average CPU below about 20-40% and peak below about 60% over several weeks
  (pick thresholds per workload type).
- Memory is rarely the bottleneck but drives the instance family choice.

## Steps

1. Inventory: call `multicloud__discover_resources` for `compute` and
   `database` to list instances by provider, region, and type.
2. Rank: call `finops__breakdown` by `service` and `account` and start with the
   largest spend.
3. Collect utilization for at least 14 days, preferably 30, including a business
   peak:
   - AWS: Compute Optimizer and CloudWatch (memory needs the CloudWatch agent).
   - Azure: Advisor recommendations and Azure Monitor metrics.
   - GCP: Recommender machine-type recommendations.
4. Choose the target: smaller size in the same family, a newer generation, or a
   different family (compute, memory, or burstable). Check licensing, network
   bandwidth, and storage throughput limits of the target size.
5. Change non-production first, then production in a maintenance window, with
   a rollback plan.
6. Verify after two weeks: performance metrics held, and `finops__compare`
   shows the reduction.

## KPIs

- Average CPU and memory utilization of the fleet.
- Monthly savings achieved versus identified.
- Share of instances on the current generation.

## Pitfalls

- Averages hide peaks; use percentiles.
- Some sizes change network or disk limits, not just CPU and memory.
- Licensed software (databases, Windows) may be priced per core; check terms.
- Autoscaling groups need their launch template changed, not single instances.
