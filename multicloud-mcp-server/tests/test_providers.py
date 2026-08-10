"""Tests for provider adapters."""

from multicloud_mcp.providers.aws import AWSProvider
from multicloud_mcp.providers.azure import AzureProvider


def test_aws_provider_namespacing():
    provider = AWSProvider()
    assert provider._namespaced_name("list_buckets") == "aws__list_buckets"
    assert provider._original_name("aws__list_buckets") == "list_buckets"


def test_azure_provider_namespacing():
    provider = AzureProvider()
    assert provider._namespaced_name("list_vms") == "azure__list_vms"
    assert provider._original_name("azure__list_vms") == "list_vms"


def test_provider_health_initial_state():
    from multicloud_mcp.providers.base import ProviderHealth

    health = ProviderHealth()
    assert health.healthy is False
    assert health.tools_count == 0
