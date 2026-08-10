# Security

Treat Multicloud MCP as a privileged gateway between AI agents and cloud infrastructure.

## HTTP authentication
Optional Bearer authentication protects `/mcp`. The API key is sourced from the environment variable configured by `api_key_env`. Token comparison is constant-time and tokens must not be logged.

## Endpoints
- `/mcp`: protected when auth enabled
- `/health`: public
- `/metrics`: protected by default when auth enabled

## Controls
- restrictive CORS
- request-size limit
- per-IP in-memory rate limiting
- `X-Request-ID` correlation
- safe external errors
- security headers
- `Cache-Control: no-store`
- structured audit logging
- sensitive-value redaction

## Tool safety
Modes: `allow_all`, `read_only`. The read-only policy blocks provider-native tool names that indicate mutating operations. It complements, not replaces, AWS IAM/Azure RBAC.

## Deployment
HTTP defaults to `127.0.0.1`. For external access, explicitly bind externally, terminate TLS at a reverse proxy/ingress/API gateway/load balancer, apply network controls, and use least-privilege cloud identities.

## Supply chain and releases

CI runs tests, coverage, Ruff, strict mypy, package build, `pip-audit`, Gitleaks and Trivy. CodeQL runs on pull requests, pushes to `main` and weekly. Dependabot checks pip, Docker and GitHub Actions weekly. Dependency Review checks pull requests that change manifests, lockfiles or workflows for vulnerable additions and license changes; license findings are advisory until a formal policy is adopted.

Actions are pinned to full commit SHAs. Releases use `vMAJOR.MINOR.PATCH`, generate Python and container SBOMs, SHA-256 checksums and GitHub provenance attestations. The release workflow does not publish to PyPI or a container registry automatically.

Enable Private Vulnerability Reporting and recommended `main` branch protection in GitHub settings; these settings are not claimed to be active until verified there.
