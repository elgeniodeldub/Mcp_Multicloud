# FinOps playbooks: how to ask and how to use them

`finops__playbooks` serves ten FinOps Framework playbooks. A playbook tells the
agent what to do; the other `finops__*` and `multicloud__*` tools return your
own numbers. This guide shows, for each playbook, questions you can ask an AI
assistant connected to this server, and the tool calls the assistant should
make to answer them.

The example questions work in any MCP client (Claude, Cursor, Hermes, and
others). The JSON blocks are the tool arguments; you can also send them
directly from an MCP inspector or a script. Dates are examples only.

## How to ask

You do not need to name the tool. Questions that work well:

- describe the goal: "How do I start allocating our cloud costs to teams?"
- ask for a playbook by topic: "Use the FinOps playbook for commitments."
- ask for a plan grounded in data: "Follow the rightsizing playbook and check
  our compute spend."

If the assistant answers from general knowledge instead of the playbooks, say
so directly: "Check the FinOps playbooks first" or "Use `finops__playbooks`".

The usual flow is:

1. `finops__playbooks` with `action: search` (or `list`) to find the playbook;
2. `finops__playbooks` with `action: get` to read its steps;
3. the tools listed in the playbook's `related_tools` to get your data;
4. the assistant combines both into an answer.

## Using the tool directly

List every playbook (summaries only, no body):

```json
{"action": "list"}
```

Filter the list by domain, phase, provider, or capability:

```json
{"action": "list", "domain": "Optimize Usage & Cost", "provider": "azure"}
```

```json
{"action": "list", "phase": "operate"}
```

```json
{"action": "list", "capability": "Rate Optimization"}
```

Search by keywords (best match first, `limit` 1-10, default 5):

```json
{"action": "search", "query": "untagged spend by team", "limit": 3}
```

Read one playbook in full:

```json
{"action": "get", "id": "cost-allocation-tagging"}
```

Every result has `content_type: "guidance"` and a `limitations` list. Each
playbook includes `related_tools`, the tools that fetch the data it needs.

| Domain | Playbook id |
|---|---|
| Understand Usage & Cost | `cost-allocation-tagging`, `anomaly-management` |
| Quantify Business Value | `budgeting-and-forecasting`, `unit-economics` |
| Optimize Usage & Cost | `rightsizing-compute`, `idle-and-orphaned-resources`, `commitment-based-discounts`, `storage-optimization` |
| Manage the FinOps Practice | `showback-and-chargeback`, `policy-and-governance` |

---

## Cost allocation and tagging

`cost-allocation-tagging`: attribute spend to owners and measure what is still
unallocated.

**Ask like this**

- "How much of last month's spend has no `team` tag?"
- "Help me design a tagging standard for our AWS and Azure accounts."
- "Which services hold most of our untagged cost?"

**Calls the assistant makes**

```json
{"action": "get", "id": "cost-allocation-tagging"}
```

`finops__cost_by_tag`: spend per value of the owner tag; untagged spend shows
as `(untagged)`.

```json
{"tag_key": "team", "period": "previous_month"}
```

`finops__breakdown`: where the untagged spend sits.

```json
{"group_by": "service", "period": "previous_month"}
```

```json
{"group_by": "account", "period": "previous_month"}
```

**What you get:** the untagged share of spend, the services and accounts that
carry it, and a tagging schema and enforcement plan from the playbook steps.

---

## Cost anomaly management

`anomaly-management`: find unexpected spend early and route it to an owner.

**Ask like this**

- "Did we have any cost spikes in the last 30 days?"
- "Why did our Azure bill jump this week?"
- "Set up an anomaly triage process for our team."

**Calls the assistant makes**

```json
{"action": "get", "id": "anomaly-management"}
```

`finops__anomalies`: findings sorted by impact; `min_impact` hides small ones.

```json
{"period": "last_30_days", "min_impact": 100}
```

`finops__breakdown`: the service and region behind a spike (use the anomaly
dates).

```json
{"group_by": "service", "start_date": "2026-10-20", "end_date": "2026-10-27"}
```

`finops__cost_by_tag`: the owning team.

```json
{"tag_key": "team", "start_date": "2026-10-20", "end_date": "2026-10-27"}
```

`finops__compare`: size of the change against the previous period.

```json
{"period": "month_to_date"}
```

**What you get:** a list of anomalies with likely source and owner, and for
each one a classification (expected, waste, unknown) and next step.

---

## Budgeting and forecasting

`budgeting-and-forecasting`: set budgets per owner and act on variance before
month end.

**Ask like this**

- "Will we stay within budget this month?"
- "Forecast our AWS and Azure spend to the end of the quarter."
- "Which budgets are close to their limit?"

**Calls the assistant makes**

```json
{"action": "get", "id": "budgeting-and-forecasting"}
```

`finops__budgets`: limit, actual, forecast, and `alert` per budget.

```json
{"alert_threshold_pct": 80}
```

`finops__forecast`: spend to a future date (defaults to the end of this month).

```json
{"start_date": "2026-11-14", "end_date": "2027-01-01", "providers": ["aws", "azure"]}
```

`finops__get_cost` and `finops__compare`: the baseline and its trend.

```json
{"period": "previous_month", "metric": "effective_cost"}
```

```json
{"period": "month_to_date"}
```

**What you get:** budgets at risk, forecast versus budget, the trend, and the
review steps (reduce, accept and re-forecast, or request more budget).

---

## Rightsizing compute

`rightsizing-compute`: match instance sizes to measured demand.

**Ask like this**

- "Which of our VMs are oversized?"
- "Give me a rightsizing plan for EC2, starting with the biggest spend."
- "Should we rightsize before buying Savings Plans?"

**Calls the assistant makes**

```json
{"action": "get", "id": "rightsizing-compute"}
```

`multicloud__discover_resources`: compute and database inventory.

```json
{"resource_types": ["compute", "database"], "providers": ["aws", "azure"]}
```

`finops__breakdown`: rank by spend.

```json
{"group_by": "service", "period": "last_30_days", "limit": 10}
```

`multicloud__map_resource`: equivalent service in the other cloud, when
relevant for migration planning.

**What you get:** the largest compute and database spend, the inventory to
review, and a step-by-step plan. Utilization data comes from provider tools
(Compute Optimizer, Azure Advisor, GCP Recommender); the playbook says where.

---

## Idle and orphaned resources

`idle-and-orphaned-resources`: remove resources that cost money and do no work.

**Ask like this**

- "Find waste we can clean up this week."
- "Do we have unattached disks or unused IP addresses?"
- "Create a monthly clean-up process for non-production accounts."

**Calls the assistant makes**

```json
{"action": "search", "query": "unattached disks snapshots idle", "limit": 3}
```

```json
{"action": "get", "id": "idle-and-orphaned-resources"}
```

`multicloud__discover_resources`: compute and storage inventory.

```json
{"resource_types": ["compute", "storage"]}
```

`finops__cost_by_tag`: owners to notify.

```json
{"tag_key": "owner", "period": "month_to_date"}
```

**What you get:** a candidate list by type, owners to confirm with, and a safe
clean-up order (notify, snapshot if needed, delete or schedule). This server is
read-only; the deletions happen in your own change process.

---

## Commitment-based discounts

`commitment-based-discounts`: buy reservations and savings plans for the stable
baseline.

**Ask like this**

- "Should we buy Savings Plans or Reserved Instances?"
- "How much of our compute spend is steady enough to commit?"
- "What's the right way to buy Azure reservations?"

**Calls the assistant makes**

```json
{"action": "search", "query": "savings plans reservations", "limit": 1}
```

```json
{"action": "get", "id": "commitment-based-discounts"}
```

`finops__breakdown`: baseline by service and region over several months.

```json
{"group_by": "service", "start_date": "2026-05-01", "end_date": "2026-11-01"}
```

```json
{"group_by": "region", "start_date": "2026-05-01", "end_date": "2026-11-01"}
```

`finops__forecast`: whether the baseline will hold.

```json
{"providers": ["aws", "azure"]}
```

`finops__get_cost`: amortized versus billed cost, to see current commitments.

```json
{"period": "previous_month", "metric": "effective_cost"}
```

```json
{"period": "previous_month", "metric": "billed_cost"}
```

**What you get:** the steady baseline, the instrument options per provider,
and a staged purchase plan. The playbook gives no discount rates; use provider
calculators and your own agreements.

---

## Storage optimization

`storage-optimization`: lifecycle tiering, retention limits, and disk types.

**Ask like this**

- "Our S3 bill keeps growing. What should we do?"
- "Which storage should move to cool or archive tiers?"
- "Set a snapshot retention policy for us."

**Calls the assistant makes**

```json
{"action": "get", "id": "storage-optimization"}
```

`multicloud__discover_resources`: storage inventory.

```json
{"resource_types": ["storage"]}
```

`finops__breakdown`: storage spend by service and account.

```json
{"group_by": "service", "period": "last_30_days"}
```

`finops__compare`: month-over-month growth.

```json
{"period": "current_month"}
```

**What you get:** where storage cost grows, the lifecycle rules to apply per
provider, and the retrieval and minimum-duration charges to check first.

---

## Unit economics

`unit-economics`: cost per customer, transaction, or request.

**Ask like this**

- "What does it cost us to serve one customer?"
- "Is our cloud spend growing faster than our usage?"
- "Help me define unit cost KPIs for our product."

**Calls the assistant makes**

```json
{"action": "get", "id": "unit-economics"}
```

`finops__cost_by_tag`: cost of the product.

```json
{"tag_key": "application", "period": "previous_month"}
```

`finops__compare`: trend between periods.

```json
{
  "start_date": "2026-10-01", "end_date": "2026-11-01",
  "compare_start_date": "2026-09-01", "compare_end_date": "2026-10-01"
}
```

**What you get:** the product's allocated cost and a unit cost formula. You
supply the business metric (customers, orders, API calls); the server has no
access to business data.

---

## Showback and chargeback

`showback-and-chargeback`: report cost to each team, then bill it internally.

**Ask like this**

- "Build a monthly cost report per team."
- "Are we ready to move from showback to chargeback?"
- "How should we share commitment savings between teams?"

**Calls the assistant makes**

```json
{"action": "get", "id": "showback-and-chargeback"}
```

`finops__cost_by_tag`: spend per team, and the untagged share.

```json
{"tag_key": "team", "period": "previous_month"}
```

`finops__get_cost`, `finops__compare`, and `finops__breakdown`: totals, trend,
and top services for the report.

```json
{"period": "previous_month", "metric": "effective_cost"}
```

```json
{"group_by": "service", "period": "previous_month", "limit": 5}
```

**What you get:** a per-team report layout, a reconciliation check against the
invoice, and readiness criteria for chargeback. Accounting treatment is a
finance decision.

---

## Policy and governance guardrails

`policy-and-governance`: turn FinOps decisions into enforced guardrails.

**Ask like this**

- "What cost guardrails should every new subscription have?"
- "Untagged resources keep coming back. How do we stop it?"
- "Which accounts have no budget?"

**Calls the assistant makes**

```json
{"action": "get", "id": "policy-and-governance"}
```

`finops__budgets`: accounts and subscriptions with and without budgets.

```json
{}
```

`finops__cost_by_tag`: whether untagged spend returns.

```json
{"tag_key": "owner", "period": "month_to_date"}
```

`multicloud__compliance_check` and `multicloud__security_posture`: control gaps
that overlap with cost controls.

```json
{"framework": "CIS", "providers": ["aws", "azure"]}
```

**What you get:** a guardrail list with owners, the audit-then-enforce order
per provider (AWS Organizations and SCPs, Azure Policy, GCP organization
policies), and the current gaps.

---

## Combined questions

One question can use several playbooks. Examples:

- "Give me a 90-day FinOps plan." The assistant lists the playbooks, then
  orders them: allocation, anomalies, idle resources, rightsizing,
  commitments.
- "Our bill rose 20% this quarter. What happened and what should we do?" Uses
  `anomaly-management`, then `rightsizing-compute` or
  `idle-and-orphaned-resources`, depending on what the breakdown shows.
- "Prepare the monthly FinOps review." Uses `budgeting-and-forecasting`,
  `anomaly-management`, and `showback-and-chargeback`.

## Limits

- Playbooks are guidance. They read no account and contain no prices.
- Actual cost tools cover AWS and Azure. For GCP, the playbooks name the GCP
  feature to use in your own console or billing export.
- Results depend on the IAM and RBAC permissions of the server's identities.
- The playbooks are aligned with the FinOps Foundation framework; they are not
  endorsed by it.
