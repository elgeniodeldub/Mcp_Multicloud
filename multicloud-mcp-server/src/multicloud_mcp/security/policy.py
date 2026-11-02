"""Centralized tool safety policy."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterable
from typing import Any


class ToolBlockedError(Exception):
    """Raised when a tool is blocked by the configured safety policy."""

    def __init__(self, tool_name: str, policy: str, reason: str = "") -> None:
        detail = f": {reason}" if reason else ""
        super().__init__(f"Tool '{tool_name}' is blocked by policy '{policy}'{detail}")
        self.tool_name = tool_name
        self.policy = policy
        self.reason = reason


class ToolSecurityPolicy:
    """Allow all tools, or allow only tools proven read-only.

    ``read_only`` is default-deny for provider passthrough tools. A passthrough
    tool runs only when it is explicitly allowlisted or its upstream server marks
    it ``readOnlyHint``, and in both cases its name and command-like arguments
    must not contain a mutating verb. Native ``multicloud__``/``finops__`` tools
    are read-only by construction.
    """

    _MUTATING_VERBS = (
        "create",
        "delete",
        "remove",
        "terminate",
        "stop",
        "start",
        "restart",
        "reboot",
        "update",
        "modify",
        "put",
        "patch",
        "set",
        "attach",
        "detach",
        "associate",
        "disassociate",
        "enable",
        "disable",
        "invoke",
        "run",
        "execute",
        "exec",
        "deploy",
        "scale",
        "write",
        "upload",
        "assign",
        "grant",
        "revoke",
        "purge",
        "import",
        "add",
        "apply",
        "rotate",
        "reset",
        "tag",
        "untag",
    )
    # Argument keys through which multiplexed tools (for example Azure MCP's
    # namespace tools) select the operation they perform.
    _COMMAND_KEYS = frozenset(
        {"command", "operation", "action", "method", "intent", "subcommand", "verb"}
    )

    def __init__(
        self,
        mode: str = "allow_all",
        allowed_tools: Iterable[str] = (),
        trust_read_only_hints: bool = True,
    ) -> None:
        if mode not in {"allow_all", "read_only"}:
            raise ValueError("security.tool_policy.mode must be 'allow_all' or 'read_only'")
        self.mode = mode
        self.allowed_tools = tuple(allowed_tools)
        self.trust_read_only_hints = trust_read_only_hints
        # Verbs match only as whole words separated by non-letters, so
        # "list_tags" or "get_settings" are not mistaken for "tag" or "set".
        self._mutating = re.compile(
            r"(?:^|[^a-z])(?:" + "|".join(self._MUTATING_VERBS) + r")(?:$|[^a-z])", re.I
        )

    def authorize_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        read_only_hint: bool | None = None,
    ) -> None:
        if self.mode == "allow_all" or tool_name.startswith(("multicloud__", "finops__")):
            return
        if self._is_mutating(tool_name.split("__", 1)[-1]):
            raise ToolBlockedError(tool_name, self.mode, "tool name indicates a mutation")
        allowlisted = any(fnmatch.fnmatchcase(tool_name, rule) for rule in self.allowed_tools)
        hinted = self.trust_read_only_hints and read_only_hint is True
        if not (allowlisted or hinted):
            raise ToolBlockedError(
                tool_name, self.mode, "tool is not allowlisted or annotated read-only"
            )
        command = self._mutating_argument(arguments or {})
        if command is not None:
            raise ToolBlockedError(tool_name, self.mode, f"argument '{command}' is mutating")

    def _is_mutating(self, value: str) -> bool:
        return bool(self._mutating.search(value))

    def _mutating_argument(self, arguments: dict[str, Any], depth: int = 0) -> str | None:
        if depth > 4:
            return None
        for key, value in arguments.items():
            if isinstance(value, dict):
                nested = self._mutating_argument(value, depth + 1)
                if nested is not None:
                    return nested
            elif (
                str(key).lower() in self._COMMAND_KEYS
                and isinstance(value, str)
                and self._is_mutating(value)
            ):
                return str(key)
        return None
