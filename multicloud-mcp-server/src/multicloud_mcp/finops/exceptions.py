"""Domain errors for live FinOps queries."""


class FinOpsError(Exception):
    """Base error exposed by the FinOps bounded context."""


class FinOpsProviderUnavailableError(FinOpsError):
    """A provider could not be queried."""


class FinOpsQueryError(FinOpsError):
    """A provider rejected or could not execute a query."""


class UnsupportedFinOpsDimensionError(FinOpsError):
    """A dimension is not supported by a provider/query combination."""


class UnsupportedFinOpsMetricError(FinOpsError):
    """A provider cannot supply the requested metric."""
