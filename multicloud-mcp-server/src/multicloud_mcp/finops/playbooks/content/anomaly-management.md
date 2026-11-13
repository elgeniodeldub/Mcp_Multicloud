---
id: anomaly-management
title: Cost anomaly management
summary: Detect unexpected spend early, triage it to an owner, and decide whether to fix, accept, or re-baseline.
domain: Understand Usage & Cost
capabilities: [Anomaly Management]
phases: [inform, operate]
providers: [aws, azure, gcp]
related_tools: [finops__anomalies, finops__breakdown, finops__compare, finops__cost_by_tag]
tags: [anomaly, spike, alert, unexpected, triage, incident, root cause]
---
# Cost anomaly management

An anomaly is spend that differs from what the owner expected. The goal is to
find it in days, not at the monthly invoice.

## When to use

- A monthly bill surprised someone.
- You have no alert that fires before month end.
- Alerts exist but nobody owns the triage.

## Signals

- `finops__anomalies` returns findings with a large absolute impact.
- `finops__compare` shows a large percentage change between periods.
- A service appears in the top of `finops__breakdown` that was not there before.

## Steps

1. Turn on detection:
   - AWS: create a Cost Anomaly Detection monitor (per service or per linked
     account) and a subscription for alerts.
   - Azure: `finops__anomalies` scores daily actual cost against a robust
     baseline; Cost Management anomaly alerts can also notify by email.
   - GCP: use budget alerts and billing export queries; GCP actual cost is not
     available through this server.
2. Pull findings: call `finops__anomalies` for `last_30_days`, sorted by impact.
   Set `min_impact` so only findings worth a person's time remain.
3. Locate the source: call `finops__breakdown` by `service`, `region`, and
   `account` for the anomaly window; call `finops__cost_by_tag` with the owner
   key to find the team.
4. Classify each finding:
   - expected (launch, migration, seasonal peak): record it and re-baseline;
   - waste (forgotten test load, runaway job, misconfiguration): fix and record
     the cause;
   - unknown: escalate to the account owner within an agreed time.
5. Close the loop: write a short note per finding (cause, owner, action,
   avoided cost) and review the list in the regular FinOps meeting.

## KPIs

- Time from anomaly start to detection.
- Time from detection to owner acknowledgement.
- Share of anomalies with a recorded root cause.

## Pitfalls

- Thresholds set too low create alert fatigue; start high and lower them.
- Daily billing data is delayed by hours or more; detection is never real time.
- An alert without a named owner is not a process.
- Credits, refunds, and month-start commitment fees can look like anomalies.
