---
id: idle-and-orphaned-resources
title: Idle and orphaned resources
summary: Find and remove resources that cost money but do no work, such as unattached disks, stopped instances with storage, idle load balancers, and old snapshots.
domain: Optimize Usage & Cost
capabilities: [Workload Optimization, Cloud Sustainability]
phases: [optimize, operate]
providers: [aws, azure, gcp]
related_tools: [multicloud__discover_resources, finops__breakdown, finops__cost_by_tag]
tags: [idle, orphaned, unattached, waste, cleanup, snapshot, disk, ip address, zombie]
---
# Idle and orphaned resources

Idle resources are the quickest savings with the lowest risk, if each deletion
is confirmed with an owner.

## When to use

- No regular clean-up process exists.
- Projects or environments were shut down but their resources remain.
- You need early savings while larger work (commitments, rightsizing) is planned.

## Signals

Common candidates on every provider:

- unattached block disks (EBS volumes, Azure managed disks, GCP persistent disks);
- snapshots and images older than the retention policy;
- reserved public IP addresses not attached to anything;
- load balancers and NAT gateways with no or very little traffic;
- stopped instances that still pay for attached storage;
- non-production environments running nights and weekends.

## Steps

1. Inventory: call `multicloud__discover_resources` for `compute` and
   `storage`.
2. Use provider findings for idle signals:
   - AWS: Trusted Advisor and Compute Optimizer idle findings.
   - Azure: Advisor cost recommendations.
   - GCP: Recommender idle resource recommendations.
3. Find the owner: call `finops__cost_by_tag` with the owner key; untagged items
   go to the account owner.
4. Notify and wait: give owners a fixed period (for example 7-14 days) to object.
5. Act safely: snapshot or export before deleting where data might matter, then
   delete. For non-production compute, schedule stop and start instead.
6. Prevent recurrence: delete-on-termination for disks, retention policies for
   snapshots, and expiry tags for temporary environments.
7. Repeat monthly and track savings with `finops__breakdown`.

## KPIs

- Monthly cost of identified idle resources (trend down).
- Average age of unattached disks and unused IP addresses.
- Share of non-production compute on a schedule.

## Pitfalls

- "Idle" by metrics may still be needed (disaster recovery, quarterly jobs).
  Confirm with the owner.
- Deleting a snapshot can remove the only backup.
- This server's tools are read-only; deletion is done in your own change
  process, never through this MCP server.
