"""Security posture analysis across clouds."""

from __future__ import annotations

from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo

logger = structlog.get_logger()

SECURITY_TOOL_SUFFIXES = (
    "iam__list_roles", "iam__list_users", "iam__get_account_authorization_details",
    "s3__list_buckets", "ec2__describe_security_groups", "security__list_findings",
    "security__get_security_score", "authorization__list_role_assignments",
    "security__list_recommendations",
)


class SecurityPostureTool:
    """Analyze security posture across connected cloud providers."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__security_posture",
            description="Analyze security configurations across AWS and Azure (public buckets, open security groups, etc.)",
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
            available = {tool.name for tool in provider.tools}
            for suffix in SECURITY_TOOL_SUFFIXES:
                tool_name = f"{provider_name}__{suffix}"
                if tool_name not in available:
                    continue
                try:
                    result = await router.call_tool(tool_name, {})
                    findings.append({"provider": provider_name, "tool": tool_name,
                                     "status": "error" if result.get("isError") else "ok",
                                     "data": result.get("content", result)})
                except Exception as exc:
                    logger.warning("security_check_failed", provider=provider_name,
                                   tool=tool_name, error=str(exc))
                    errors.append({"provider": provider_name, "tool": tool_name, "error": str(exc)})
        summary = {"providers_checked": len(selected), "checks_run": len(findings),
                   "errors": len(errors)}
        return {"findings": findings, "errors": errors, "summary": summary}
