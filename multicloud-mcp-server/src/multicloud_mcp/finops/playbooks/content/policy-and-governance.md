---
id: policy-and-governance
title: Policy and governance guardrails
summary: Turn FinOps decisions into preventive guardrails, such as tagging rules, allowed regions and sizes, and budget alerts, enforced in the cloud platforms.
domain: Manage the FinOps Practice
capabilities: [Policy & Governance, FinOps Practice Operations]
phases: [operate]
providers: [aws, azure, gcp]
related_tools: [multicloud__compliance_check, multicloud__security_posture, finops__budgets, finops__cost_by_tag]
tags: [policy, governance, guardrail, azure policy, scp, organization policy, enforcement, quota]
---
# Policy and governance guardrails

Reviews find waste after it happens. Guardrails stop common waste before it
starts, at a lower cost of attention.

## When to use

- The same findings return every month (untagged resources, oversized test
  machines, unused regions).
- New accounts or subscriptions are created without budgets or owners.
- You are setting up a landing zone or platform team.

## Signals

- `finops__cost_by_tag` shows untagged spend returning after clean-ups.
- `finops__budgets` shows accounts with no budget.
- `multicloud__compliance_check` reports control gaps in the same areas.

## Steps

1. List the decisions to enforce, each with an owner and an exception process:
   required tags, allowed regions, allowed instance families or sizes for
   non-production, mandatory budgets per account.
2. Start in audit mode, then enforce:
   - AWS: Organizations tag policies and service control policies; AWS Config
     rules for detection.
   - Azure: Azure Policy with `audit`, then `deny` or `modify`, assigned at
     management-group scope.
   - GCP: organization policy constraints, such as resource location limits.
3. Make every new account or subscription start with an owner tag, a budget,
   and alerts (account vending or landing-zone automation).
4. Check posture regularly: call `multicloud__compliance_check` and
   `multicloud__security_posture`; many cost controls (no public unused IPs,
   logging retention) overlap with security controls.
5. Review exceptions quarterly and remove the ones no longer needed.

## KPIs

- Share of accounts or subscriptions with an owner and a budget.
- Policy compliance rate per guardrail.
- Number of open exceptions and their age.

## Pitfalls

- Enforcing `deny` without an audit period breaks deployments.
- Guardrails without an exception process push teams to work around them.
- This server's policy layer and these playbooks complement, and do not
  replace, IAM, RBAC, and provider policy engines.
