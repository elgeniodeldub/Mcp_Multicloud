"""Compliance checking across clouds."""

from __future__ import annotations

from typing import Any

import structlog

from multicloud_mcp.providers.base import ToolInfo
from multicloud_mcp.tools.security_posture import SecurityPostureTool

logger = structlog.get_logger()


class ComplianceCheckerTool:
    """Check compliance against frameworks like CIS or NIST."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__compliance_check",
            description="Verify cloud compliance against CIS or NIST frameworks across AWS and Azure.",
            input_schema={
                "type": "object",
                "required": ["framework"],
                "properties": {
                    "framework": {
                        "type": "string",
                        "enum": ["CIS", "NIST"],
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["aws", "azure"]},
                    },
                },
            },
            original_name="multicloud__compliance_check",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any], router: Any = None) -> dict[str, Any]:
        """Execute compliance check."""
        framework = str(arguments.get("framework", "CIS")).upper()
        if framework not in {"CIS", "NIST"}:
            return {
                "framework": framework,
                "status": "invalid",
                "checks": [],
                "errors": [{"error": "framework must be CIS or NIST"}],
            }
        posture = await SecurityPostureTool().execute(arguments, router)
        checks = [
            {
                "control": "identity_and_access",
                "framework": framework,
                "status": "review" if posture["findings"] else "not_evaluated",
                "description": "Review IAM and role assignments for least privilege.",
            },
            {
                "control": "network_and_data_protection",
                "framework": framework,
                "status": "review" if posture["findings"] else "not_evaluated",
                "description": "Review public exposure and security group settings.",
            },
        ]
        logger.info(
            "compliance_checked",
            framework=framework,
            checks=len(checks),
            errors=len(posture["errors"]),
        )
        return {
            "framework": framework,
            "status": "review_required" if posture["errors"] else "evaluated",
            "checks": checks,
            "findings": posture["findings"],
            "errors": posture["errors"],
        }
