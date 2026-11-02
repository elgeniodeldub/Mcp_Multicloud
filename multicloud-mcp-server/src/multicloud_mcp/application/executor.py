"""Shared native/provider tool execution boundary."""

from __future__ import annotations

import fnmatch
import time
from typing import Any

import structlog

from multicloud_mcp.application.context import ExecutionContext
from multicloud_mcp.application.results import ApplicationError, ToolExecutionResult
from multicloud_mcp.domain.exceptions import (
    AuthenticationError,
    ProviderUnavailableError,
    RateLimitError,
)
from multicloud_mcp.finops.exceptions import FinOpsError, FinOpsProviderUnavailableError
from multicloud_mcp.observability import ToolMetrics, Tracer
from multicloud_mcp.router import ProviderRouter, ToolNotFoundError
from multicloud_mcp.security import ToolBlockedError, ToolSecurityPolicy
from multicloud_mcp.security.auth import InsufficientScopeError
from multicloud_mcp.tools.registry import NativeToolRegistry

logger = structlog.get_logger()


class ApplicationToolExecutor:
    """Execute native and passthrough tools through one transport-neutral path."""

    def __init__(
        self,
        native_tools: NativeToolRegistry,
        router: ProviderRouter,
        security_policy: ToolSecurityPolicy,
        tool_scopes: dict[str, str] | None = None,
        metrics: ToolMetrics | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.native_tools = native_tools
        self.router = router
        self.security_policy = security_policy
        self.tool_scopes = tool_scopes or {}
        self.metrics = metrics or ToolMetrics()
        self.tracer = tracer or Tracer()

    def authorize_scopes(self, name: str, context: ExecutionContext) -> None:
        """Require the OAuth scope mapped to this tool when the caller has a token."""
        if context.scopes is None:
            return
        for pattern, scope in self.tool_scopes.items():
            if fnmatch.fnmatchcase(name, pattern):
                if scope not in context.scopes:
                    raise InsufficientScopeError(f"Tool '{name}' requires scope '{scope}'")
                return
        raise InsufficientScopeError(f"Tool '{name}' has no scope mapping")

    async def execute(
        self, name: str, arguments: dict[str, Any], context: ExecutionContext
    ) -> ToolExecutionResult:
        with self.tracer.span(
            "mcp.tool_call",
            tool=name,
            transport=context.transport,
            request_id=context.request_id,
            caller=context.caller,
        ) as span:
            result = await self._execute(name, arguments, context)
            outcome = result.errors[0].code if result.errors else "success"
            self.metrics.observe(name, outcome, result.duration_ms or 0.0)
            if span is not None:
                span.set_attribute("mcp.outcome", outcome)
            return result

    async def _execute(
        self, name: str, arguments: dict[str, Any], context: ExecutionContext
    ) -> ToolExecutionResult:
        started = time.perf_counter()
        provider = name.split("__", 1)[0] if "__" in name else None
        try:
            native = self.native_tools.get_optional(name)
            self.authorize_scopes(name, context)
            if native is None:
                await self.router.refresh_tools()
                info = self.router.get_tool_info(name)
                self.security_policy.authorize_tool(
                    name, arguments, info.read_only_hint if info else None
                )
            data = (
                await native.execute(arguments)
                if native is not None
                else await self.router.call_tool(name, arguments)
            )
            result = ToolExecutionResult(
                data=data,
                providers=[provider] if provider else [],
                request_id=context.request_id,
            )
        except InsufficientScopeError as error:
            result = self._error("insufficient_scope", str(error), context, provider)
        except ToolBlockedError as error:
            result = self._error("tool_blocked_by_policy", str(error), context, provider)
        except ToolNotFoundError as error:
            result = self._error("tool_not_found", str(error), context, provider)
        except AuthenticationError as error:
            result = self._error("authentication_error", str(error), context, provider)
        except RateLimitError as error:
            result = self._error("rate_limited", str(error), context, provider)
        except (ProviderUnavailableError, FinOpsProviderUnavailableError) as error:
            result = self._error("provider_unavailable", str(error), context, provider)
        except FinOpsError as error:
            result = self._error("invalid_request", str(error), context, provider)
        except TimeoutError:
            result = self._error("timeout", "Tool execution timed out", context, provider)
        except Exception:
            result = self._error("upstream_error", "Tool execution failed", context, provider)
        result.duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "application_tool_execution",
            request_id=context.request_id,
            tool=name,
            provider=provider,
            transport=context.transport,
            caller=context.caller,
            success=not result.errors,
            partial=result.partial,
            duration_ms=result.duration_ms,
            error_type=result.errors[0].code if result.errors else None,
        )
        return result

    @staticmethod
    def _error(
        code: str, message: str, context: ExecutionContext, provider: str | None
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            errors=[ApplicationError(code, message, provider)],
            partial=False,
            providers=[provider] if provider else [],
            request_id=context.request_id,
        )
