"""Resource mapping tool between cloud providers."""

from __future__ import annotations

from typing import Any

from multicloud_mcp.providers.base import ToolInfo


class ResourceMapperTool:
    """Map cloud resources between AWS and Azure."""

    def get_tool_info(self) -> ToolInfo:
        return ToolInfo(
            name="multicloud__map_resource",
            description=(
                "Read-only mapping of an AWS or Azure resource type to its equivalent "
                "service in the other provider. Use for migration planning, not resource "
                "discovery or changes; returns an equivalent, confidence, and notes. "
                "GCP resources are not supported by this mapper."
            ),
            input_schema={
                "type": "object",
                "required": ["source_provider", "resource_type", "target_provider"],
                "properties": {
                    "source_provider": {
                        "type": "string",
                        "enum": ["aws", "azure"],
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Resource type to map (e.g., 's3_bucket', 'aks_cluster')",
                    },
                    "target_provider": {
                        "type": "string",
                        "enum": ["aws", "azure"],
                    },
                },
            },
            original_name="multicloud__map_resource",
            provider="multicloud",
            namespace="multicloud",
        )

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute resource mapping."""
        source = str(arguments.get("source_provider", ""))
        target = str(arguments.get("target_provider", ""))
        resource = arguments.get("resource_type", "")

        mappings = {
            ("aws", "azure"): {
                "s3_bucket": "Azure Blob Storage",
                "ec2_instance": "Azure Virtual Machine",
                "eks_cluster": "Azure Kubernetes Service (AKS)",
                "lambda_function": "Azure Functions",
                "rds_postgres": "Azure Database for PostgreSQL",
                "dynamodb": "Azure Cosmos DB",
                "sqs_queue": "Azure Service Bus Queue",
                "sns_topic": "Azure Service Bus Topic",
                "cloudwatch": "Azure Monitor",
                "iam_role": "Azure Managed Identity",
                "vpc": "Azure Virtual Network",
                "route53": "Azure DNS",
                "elb": "Azure Load Balancer",
                "autoscaling_group": "Azure Virtual Machine Scale Sets",
            },
            ("azure", "aws"): {
                "blob_storage": "Amazon S3",
                "virtual_machine": "Amazon EC2",
                "aks_cluster": "Amazon EKS",
                "functions": "AWS Lambda",
                "postgresql": "Amazon RDS for PostgreSQL",
                "cosmos_db": "Amazon DynamoDB",
                "service_bus": "Amazon SQS/SNS",
                "monitor": "Amazon CloudWatch",
                "managed_identity": "AWS IAM Role",
                "virtual_network": "Amazon VPC",
                "dns": "Amazon Route 53",
                "load_balancer": "Elastic Load Balancing",
                "vm_scale_sets": "Auto Scaling Groups",
            },
        }

        key = (source, target)
        mapping = mappings.get(key, {})

        return {
            "source": {"provider": source, "resource": resource},
            "target": {"provider": target},
            "equivalent": mapping.get(resource, "No direct equivalent found"),
            "mapping_confidence": "high" if resource in mapping else "low",
            "notes": self._get_notes(resource, mapping.get(resource)),
        }

    def _get_notes(self, source_resource: str, target_resource: str | None) -> str:
        if not target_resource:
            return f"No standard mapping found for {source_resource}. Consider custom architecture review."
        notes = {
            "s3_bucket": "Azure Blob Storage supports hot/cool/archive tiers. Consider lifecycle policies.",
            "ec2_instance": "Check Azure Hybrid Benefit for Windows workloads.",
            "eks_cluster": "AKS has managed control plane. Consider Azure CNI vs. kubenet.",
            "lambda_function": "Azure Functions Consumption plan is most similar to Lambda.",
            "dynamodb": "Cosmos DB offers multi-model support. Choose API carefully.",
        }
        return notes.get(source_resource, "Review service-specific features and limitations.")
