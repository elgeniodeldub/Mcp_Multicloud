"""Backward-compatible import for the former cost comparison tool."""

from multicloud_mcp.tools.list_price_comparison import (
    CostComparisonTool,
    ListPriceComparisonTool,
)

__all__ = ["CostComparisonTool", "ListPriceComparisonTool"]
