"""MCP tool serving FinOps Framework playbooks as read-only guidance."""

from __future__ import annotations

import re
from typing import Any

import structlog

from multicloud_mcp.finops.exceptions import InvalidPlaybookRequestError
from multicloud_mcp.finops.playbooks import (
    FINOPS_DOMAINS,
    FINOPS_PHASES,
    Playbook,
    PlaybookCatalog,
    load_default_catalog,
)
from multicloud_mcp.providers.base import ToolInfo

logger = structlog.get_logger()

ACTIONS = ("list", "search", "get")
PROVIDERS = ("aws", "azure", "gcp")
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
MAX_FILTER_LENGTH = 100
DEFAULT_SEARCH_LIMIT = 5
MAX_SEARCH_LIMIT = 10
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")

LIMITATIONS = [
    "Guidance only: playbooks do not read your cloud accounts or billing data.",
    "No prices or discount rates; use finops__* cost tools for your own figures.",
    "Aligned with the FinOps Foundation framework; not endorsed by it.",
    "Not legal, tax, accounting, or procurement advice.",
]


class FinOpsPlaybooksTool:
    """List, search, and read packaged FinOps Framework playbooks."""

    def __init__(self, catalog: PlaybookCatalog | None = None) -> None:
        self.catalog = catalog or load_default_catalog()

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="finops__playbooks",
            description=(
                "Read-only FinOps Framework playbooks: step-by-step guidance for common "
                "practices (allocation and tagging, anomalies, budgets and forecasts, "
                "rightsizing, idle resources, commitments, storage, unit economics, "
                "showback/chargeback, governance). Use action=list or search to find one, "
                "then action=get for the full runbook. Each playbook names the finops__ and "
                "multicloud__ tools that fetch the data it needs. Contains no prices and "
                "reads no cloud account."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": list(ACTIONS),
                        "default": "list",
                        "description": "list summaries, search by keywords, or get one.",
                    },
                    "id": {
                        "type": "string",
                        "description": "Playbook id for action=get, e.g. cost-allocation-tagging.",
                    },
                    "query": {
                        "type": "string",
                        "minLength": MIN_QUERY_LENGTH,
                        "maxLength": MAX_QUERY_LENGTH,
                        "description": "Keywords for action=search.",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": MAX_SEARCH_LIMIT,
                        "default": DEFAULT_SEARCH_LIMIT,
                    },
                    "domain": {"type": "string", "enum": list(FINOPS_DOMAINS)},
                    "capability": {
                        "type": "string",
                        "description": "FinOps Framework capability, e.g. Rate Optimization.",
                    },
                    "phase": {"type": "string", "enum": list(FINOPS_PHASES)},
                    "provider": {"type": "string", "enum": list(PROVIDERS)},
                },
            },
            original_name="finops__playbooks",
            provider="finops",
            namespace="finops",
            read_only_hint=True,
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        action = str(arguments.get("action") or "list").lower()
        if action not in ACTIONS:
            raise InvalidPlaybookRequestError(f"action must be one of {list(ACTIONS)}")
        if action == "get":
            result = self._get(arguments)
        else:
            candidates = self._filtered(arguments)
            if action == "search":
                result = self._search(arguments, candidates)
            else:
                result = self._list(candidates)
        logger.info("finops_playbooks_served", action=action, count=result["returned_count"])
        return {
            "action": action,
            "content_type": "guidance",
            **result,
            "limitations": LIMITATIONS,
        }

    def _get(self, arguments: dict[str, Any]) -> dict[str, Any]:
        playbook_id = str(arguments.get("id") or "").strip().lower()
        if not playbook_id:
            raise InvalidPlaybookRequestError("id is required for action=get")
        if not _ID_PATTERN.match(playbook_id):
            raise InvalidPlaybookRequestError("id must use lowercase letters, digits, and '-'")
        playbook = self.catalog.get(playbook_id)
        if playbook is None:
            known = ", ".join(p.id for p in self.catalog.all())
            raise InvalidPlaybookRequestError(
                f"unknown playbook '{playbook_id}'; known ids: {known}"
            )
        return {"playbook": playbook.full_dict(), "returned_count": 1}

    def _list(self, candidates: list[Playbook]) -> dict[str, Any]:
        return {
            "playbooks": [playbook.summary_dict() for playbook in candidates],
            "returned_count": len(candidates),
        }

    def _search(self, arguments: dict[str, Any], candidates: list[Playbook]) -> dict[str, Any]:
        query = str(arguments.get("query") or "").strip()
        if not MIN_QUERY_LENGTH <= len(query) <= MAX_QUERY_LENGTH:
            raise InvalidPlaybookRequestError(
                f"query must be {MIN_QUERY_LENGTH}-{MAX_QUERY_LENGTH} characters for action=search"
            )
        limit = self._limit(arguments.get("limit", DEFAULT_SEARCH_LIMIT))
        allowed = {playbook.id for playbook in candidates}
        ranked = [pair for pair in self.catalog.search(query) if pair[0].id in allowed]
        matches = [
            {**playbook.summary_dict(), "score": score} for playbook, score in ranked[:limit]
        ]
        return {"playbooks": matches, "returned_count": len(matches), "total_matches": len(ranked)}

    @staticmethod
    def _limit(value: Any) -> int:
        try:
            limit = int(value)
        except (TypeError, ValueError) as exc:
            raise InvalidPlaybookRequestError("limit must be an integer") from exc
        if not 1 <= limit <= MAX_SEARCH_LIMIT:
            raise InvalidPlaybookRequestError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}")
        return limit

    def _filtered(self, arguments: dict[str, Any]) -> list[Playbook]:
        domain = self._filter(arguments, "domain")
        if domain and domain not in FINOPS_DOMAINS:
            raise InvalidPlaybookRequestError(f"domain must be one of {list(FINOPS_DOMAINS)}")
        phase = (self._filter(arguments, "phase") or "").lower()
        if phase and phase not in FINOPS_PHASES:
            raise InvalidPlaybookRequestError(f"phase must be one of {list(FINOPS_PHASES)}")
        provider = (self._filter(arguments, "provider") or "").lower()
        if provider and provider not in PROVIDERS:
            raise InvalidPlaybookRequestError(f"provider must be one of {list(PROVIDERS)}")
        capability = (self._filter(arguments, "capability") or "").lower()

        def keep(playbook: Playbook) -> bool:
            return (
                (not domain or playbook.domain == domain)
                and (not phase or phase in playbook.phases)
                and (not provider or provider in playbook.providers)
                and (
                    not capability or capability in (item.lower() for item in playbook.capabilities)
                )
            )

        return [playbook for playbook in self.catalog.all() if keep(playbook)]

    @staticmethod
    def _filter(arguments: dict[str, Any], key: str) -> str | None:
        value = arguments.get(key)
        if value is None or value == "":
            return None
        text = str(value).strip()
        if len(text) > MAX_FILTER_LENGTH:
            raise InvalidPlaybookRequestError(f"{key} is too long")
        return text
