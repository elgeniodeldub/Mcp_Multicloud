"""Security posture analysis across clouds."""

from __future__ import annotations

from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo
from multicloud_mcp.providers.capabilities import Capability

logger = structlog.get_logger()

LEGACY_SECURITY_SUFFIXES = (
    "list_roles",
    "list_users",
    "list_findings",
    "list_role_assignments",
)


class SecurityPostureTool:
    """Analyze security posture across connected cloud providers."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__security_posture",
            description=(
                "Read-only security posture analysis across AWS and Azure, including "
                "available exposure, IAM, findings, and capability checks. Use for "
                "security visibility, not remediation; returns findings and partial "
                "provider status. GCP security is not included."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="multicloud__security_posture",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any], router: Any = None) -> dict[str, Any]:
        """Execute security posture analysis."""
        if router is None:
            return {"findings": [], "errors": [{"error": "Router is required"}], "summary": {}}
        selected = arguments.get("providers") or list(router.providers)
        findings: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for provider_name in selected:
            provider = router.providers.get(provider_name)
            if provider is None:
                errors.append({"provider": provider_name, "error": "Provider not connected"})
                continue
            try:
                execute_capability = getattr(provider, "execute_capability", None)
                supports = getattr(provider, "supports", None)
                if (
                    callable(execute_capability)
                    and callable(supports)
                    and supports(Capability.SECURITY)
                ):
                    result = await execute_capability(Capability.SECURITY, {})
                    findings.append(
                        {
                            "provider": provider_name,
                            "tool": Capability.SECURITY.value,
                            "status": "error" if result.get("isError") else "ok",
                            "data": result.get("content", result),
                        }
                    )
                else:
                    available = {tool.name for tool in provider.tools}
                    legacy_tool = next(
                        (
                            name
                            for name in available
                            if any(name.endswith(suffix) for suffix in LEGACY_SECURITY_SUFFIXES)
                        ),
                        None,
                    )
                    if legacy_tool is None:
                        continue
                    result = await router.call_tool(legacy_tool, {})
                    findings.append(
                        {
                            "provider": provider_name,
                            "tool": legacy_tool,
                            "status": "error" if result.get("isError") else "ok",
                            "data": result.get("content", result),
                        }
                    )
            except Exception as exc:
                logger.warning(
                    "security_check_failed",
                    provider=provider_name,
                    capability=Capability.SECURITY.value,
                    error_type=type(exc).__name__,
                )
                errors.append(
                    {
                        "provider": provider_name,
                        "capability": Capability.SECURITY.value,
                        "error": type(exc).__name__,
                    }
                )
        summary = {
            "providers_checked": len(selected),
            "checks_run": len(findings),
            "errors": len(errors),
        }
        return {"findings": findings, "errors": errors, "summary": summary}
