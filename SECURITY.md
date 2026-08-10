# Security policy

## Supported versions

Only the latest release and the latest `main` revision receive security fixes. Deploy reviewed release artifacts, not arbitrary branch snapshots.

## Reporting a vulnerability

Do not open a public issue for security vulnerabilities. Use GitHub **Private vulnerability reporting** in this repository. Include the affected version or commit, impact, safe reproduction steps, and relevant logs without credentials or customer data.

Maintainers should enable Private vulnerability reporting in the repository Security settings. Reports are acknowledged, validated, fixed and disclosed in a coordinated manner when appropriate.

## Recommended branch protection

For `main`, require pull requests, at least one approval, dismissal of stale approvals, resolved conversations, up-to-date branches, required CI/CodeQL/security checks, and block force pushes and deletion. These are recommendations and are not claimed to be enabled until verified in GitHub settings.
