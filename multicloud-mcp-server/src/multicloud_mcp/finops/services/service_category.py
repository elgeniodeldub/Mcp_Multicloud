"""Small extensible cross-cloud service categorizer."""

SERVICE_CATEGORY_MAP: dict[str, tuple[str, ...]] = {
    "Compute": ("ec2", "elastic compute", "virtual machines", "compute engine", "container"),
    "Storage": ("s3", "storage", "blob", "ebs", "files"),
    "Database": ("rds", "sql", "database", "dynamodb", "cosmos", "postgres", "mysql"),
    "Networking": ("vpc", "virtual network", "load balancer", "cdn", "network"),
    "Security": ("security", "defender", "key management", "inspector", "sentinel"),
}


def normalize_service_category(provider: str, service_name: str | None) -> str:
    """Map common AWS/Azure service names to a stable category."""
    del provider
    value = (service_name or "").lower()
    for category, terms in SERVICE_CATEGORY_MAP.items():
        if any(term in value for term in terms):
            return category
    return "Other"
