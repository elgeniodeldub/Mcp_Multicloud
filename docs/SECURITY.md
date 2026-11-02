# Security

Treat Multicloud MCP as a privileged gateway between AI agents and cloud infrastructure.

## HTTP authentication
Two modes protect `/mcp` (and `/metrics` when `protect_metrics` is on):

- `type: bearer`: one static API key from the environment variable named by `api_key_env`, compared in constant time. Simple, but every caller shares one identity with full access.
- `type: oidc` (recommended): OAuth 2.1 / OpenID Connect access tokens (JWT). The server discovers the issuer's JWKS, accepts only asymmetric signatures (RS/ES/PS), and checks `iss`, `aud`, `exp`, `iat`, `sub`, and `required_scopes`. Each tool call then needs the scope mapped to it in `tool_scopes` (first matching glob wins; default `finops__*` -> `finops:read`, `multicloud__*` -> `multicloud:read`, everything else -> `provider:call`). Missing scopes return HTTP 403 `insufficient_scope`.

```yaml
security:
  authentication:
    enabled: true
    type: oidc
    oidc:
      issuer: "https://login.microsoftonline.com/<tenant-id>/v2.0"
      audience: "api://multicloud-mcp"
      required_scopes: []
      scope_claim: scp   # Entra ID uses "scp"; most IdPs use "scope"
    tool_scopes:
      "finops__*": "finops:read"
      "multicloud__*": "multicloud:read"
      "*": "provider:call"
```

The audit log records the token subject as `caller`. Tokens are never logged.

## Remote binding guard
HTTP refuses to start on a non-loopback address (for example `0.0.0.0`) unless authentication is enabled. To run unauthenticated behind a gateway that authenticates for you, set `security.allow_unauthenticated_remote: true` explicitly.

## Reverse proxies
`X-Forwarded-For` is ignored unless the direct peer is listed in `security.trusted_proxies` (IPs or CIDRs). The header is read right to left and the first untrusted hop is the client, so callers cannot spoof their address by prepending values. Rate limiting is per token subject when authenticated, otherwise per client IP. Set `security.hsts: true` when TLS terminates in front of the server.

## Endpoints
- `/mcp`: protected when auth enabled
- `/health`: public
- `/metrics`: protected by default when auth enabled

## Controls
- restrictive CORS
- request-size limit
- per-identity / per-IP rate limiting (in-memory, or Redis shared across replicas)
- `Content-Security-Policy`, `X-Frame-Options`, optional HSTS
- `X-Request-ID` correlation
- safe external errors
- security headers
- `Cache-Control: no-store`
- structured audit logging
- sensitive-value redaction

## Tool safety
Modes: `allow_all`, `read_only`. Native `finops__*` and `multicloud__*` tools are read-only by construction.

In `read_only` mode, provider passthrough tools are **denied by default**. A passthrough tool runs only if:

1. it matches `tool_policy.allowed_tools` (fnmatch globs such as `azure__monitor*`), or the upstream server annotates it `readOnlyHint: true` and `trust_read_only_hints` is on (default); and
2. neither its name nor any command-like argument (`command`, `operation`, `action`, `method`, `intent`, `subcommand`, `verb`, including nested objects) contains a mutating verb such as create, delete, update, set, start, run, deploy, grant, or tag.

Point 2 matters for multiplexed tools (Azure MCP exposes one tool per namespace and selects the operation through an argument). This policy complements, and never replaces, AWS IAM and Azure RBAC; see [least-privilege identities](least-privilege.md).

## Deployment
HTTP defaults to `127.0.0.1`. For external access, explicitly bind externally, terminate TLS at a reverse proxy/ingress/API gateway/load balancer, apply network controls, and use least-privilege cloud identities.

## Supply chain and releases

CI runs tests, coverage, Ruff, strict mypy, package build, `pip-audit`, Gitleaks and Trivy. CodeQL runs on pull requests, pushes to `main` and weekly. Dependabot checks pip, Docker and GitHub Actions weekly. Dependency Review checks pull requests that change manifests, lockfiles or workflows for vulnerable additions and license changes; license findings are advisory until a formal policy is adopted.

Actions are pinned to full commit SHAs. Releases use `vMAJOR.MINOR.PATCH`, generate Python and container SBOMs, SHA-256 checksums and GitHub provenance attestations. The release image is pushed to `ghcr.io/<owner>/multicloud-mcp-server`, signed keyless with cosign (GitHub OIDC), and carries the SPDX SBOM as a signed attestation. Verify before deploying:

```bash
cosign verify ghcr.io/elgeniodeldub/multicloud-mcp-server:v0.2.0 \
  --certificate-identity-regexp '^https://github.com/elgeniodeldub/Mcp_Multicloud/' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

The container preinstalls the pinned `@azure/mcp` release at build time (npm verifies registry integrity hashes), so nothing is downloaded with `npx -y` at runtime. The release workflow does not publish to PyPI.

Enable Private Vulnerability Reporting and recommended `main` branch protection in GitHub settings; these settings are not claimed to be active until verified there.
