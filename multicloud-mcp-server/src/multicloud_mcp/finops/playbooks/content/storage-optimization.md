---
id: storage-optimization
title: Storage optimization
summary: Lower storage cost with lifecycle tiering, retention limits, and the right disk types, without breaking access or recovery needs.
domain: Optimize Usage & Cost
capabilities: [Workload Optimization]
phases: [optimize]
providers: [aws, azure, gcp]
related_tools: [multicloud__discover_resources, finops__breakdown, finops__get_cost]
tags: [storage, s3, blob, lifecycle, tiering, archive, retention, snapshot, disk type, egress]
---
# Storage optimization

Storage grows quietly because nothing is deleted by default. Lifecycle rules
make retention a decision instead of an accident.

## When to use

- Object or file storage grows every month with no plan.
- Backup and snapshot retention is "forever".
- Block disks use premium types for workloads that do not need them.

## Signals

- `finops__breakdown` by `service` shows storage rising month over month.
- Buckets or containers with no lifecycle policy.
- Many requests or retrievals on cold tiers (wrong tier choice).

## Steps

1. Inventory: call `multicloud__discover_resources` for `storage`.
2. Rank by cost: call `finops__breakdown` by `service` and `account`.
3. Classify data by access pattern and retention need with the owners: hot,
   infrequent, archive, delete.
4. Apply lifecycle rules:
   - AWS S3: lifecycle transitions to Infrequent Access, Glacier tiers, or
     Intelligent-Tiering for unknown patterns; expiration for temporary data.
   - Azure Blob: lifecycle management to cool, cold, and archive tiers.
   - GCP Cloud Storage: Object Lifecycle Management to Nearline, Coldline, and
     Archive, or Autoclass.
5. Set snapshot and backup retention to the documented recovery need.
6. Review block disks: move to general-purpose types where performance allows
   (for example gp3 on AWS), and remove unattached disks.
7. Check data transfer: replication and egress can cost more than the storage.

## KPIs

- Cost per stored TB, by tier.
- Share of object storage under a lifecycle policy.
- Snapshot and backup storage versus the retention policy.

## Pitfalls

- Cold tiers have minimum storage durations and retrieval charges; moving
  short-lived or frequently read data there costs more.
- Lifecycle transitions themselves have request charges for many small objects.
- Legal hold and compliance retention override cost goals; confirm with owners.
