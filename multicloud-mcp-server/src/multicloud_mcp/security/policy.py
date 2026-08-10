"""Centralized tool safety policy."""

from __future__ import annotations

import re


class ToolBlockedError(Exception):
    """Raised when a tool is blocked by the configured safety policy."""

    def __init__(self, tool_name: str, policy: str) -> None:
        super().__init__(f"Tool '{tool_name}' is blocked by policy '{policy}'")
        self.tool_name = tool_name
        self.policy = policy


class ToolSecurityPolicy:
    """Allow all tools or block clearly mutating provider-native tools."""

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
        "run_command",
        "execute",
        "deploy",
        "scale",
    )

    def __init__(self, mode: str = "allow_all") -> None:
        if mode not in {"allow_all", "read_only"}:
            raise ValueError("security.tool_policy.mode must be 'allow_all' or 'read_only'")
        self.mode = mode
        self._mutating = re.compile(
            r"(?:^|__)(?:" + "|".join(self._MUTATING_VERBS) + r")(?:$|_|__)", re.I
        )

    def authorize_tool(self, tool_name: str) -> None:
        if self.mode == "allow_all" or tool_name.startswith(("multicloud__", "finops__")):
            return
        if self._mutating.search(tool_name):
            raise ToolBlockedError(tool_name, self.mode)
