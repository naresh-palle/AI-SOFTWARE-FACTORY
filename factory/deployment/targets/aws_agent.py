"""
AWS Target Deployment Agent.
Generates ECS/Fargate task definitions, ALB configurations, and S3/CloudFront manifests.
"""

from typing import Dict, Any, List


class AWSTargetAgent:
    """Manages AWS ECS/Fargate and CloudFront deployment definitions."""

    @staticmethod
    def generate_fargate_task_def(
        app_name: str,
        image_tag: str,
        cpu: int = 1024,
        memory: int = 2048,
        port: int = 8000,
        env_vars: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Generate AWS ECS Fargate task definition JSON."""
        env_list = [{"name": k, "value": v} for k, v in (env_vars or {}).items()]
        return {
            "family": f"{app_name}-service",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": str(cpu),
            "memory": str(memory),
            "containerDefinitions": [
                {
                    "name": app_name,
                    "image": image_tag,
                    "essential": True,
                    "portMappings": [{"containerPort": port, "protocol": "tcp"}],
                    "environment": env_list,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{app_name}",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "app",
                        },
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", f"curl -f http://localhost:{port}/health || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                    },
                }
            ],
        }

    @staticmethod
    def generate_cloudfront_s3_manifest(
        app_name: str,
        bucket_name: str,
        domain_name: str = None,
    ) -> Dict[str, Any]:
        """Generate S3 Static Website + CloudFront CDN distribution manifest."""
        return {
            "s3_bucket": bucket_name,
            "origin_access_control": True,
            "index_document": "index.html",
            "error_document": "index.html",
            "cloudfront_distribution": {
                "comment": f"CDN for {app_name}",
                "price_class": "PriceClass_100",
                "viewer_certificate": {
                    "acm_certificate_arn": "optional_acm_arn" if domain_name else None,
                    "ssl_support_method": "sni-only" if domain_name else None,
                    "minimum_protocol_version": "TLSv1.2_2021",
                },
                "default_cache_behavior": {
                    "viewer_protocol_policy": "redirect-to-https",
                    "allowed_methods": ["GET", "HEAD", "OPTIONS"],
                    "cached_methods": ["GET", "HEAD"],
                    "compress": True,
                },
            },
        }
