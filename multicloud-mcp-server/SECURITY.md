# Security policy

## Supported versions

Only the latest version on the `main` branch and the latest published release receive security fixes. Pin deployments to a reviewed release artifact rather than an unreviewed branch snapshot.

## Reporting a vulnerability

Please do not open a public GitHub issue for a security vulnerability. Use GitHub's **Private vulnerability reporting** feature on this repository. Include the affected version or commit, impact, reproduction steps, and any proof of concept needed to reproduce the issue safely. Do not include production credentials or sensitive customer data.

We will acknowledge reports as soon as practical, validate the issue, coordinate a fix, and publish a sanitized advisory when appropriate.

## Repository protections

Maintainers should enable Private vulnerability reporting in the repository's Security settings. Recommended protection for `main`:

- pull request required with at least one approval;
- dismiss stale approvals and require conversation resolution;
- require branches to be up to date;
- require CI, CodeQL, dependency-audit, secret-scan, and container-scan checks;
- block force pushes and branch deletion.

These settings are recommendations; they are not claimed to be enabled by this repository unless verified in GitHub settings.
