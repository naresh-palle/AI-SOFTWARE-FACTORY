output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.factory_cluster.name
  description = "ECS Fargate Cluster Name"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.worker.repository_url
  description = "ECR Repository URL for Cloud Worker"
}

output "s3_artifacts_bucket" {
  value       = aws_s3_bucket.artifacts.bucket
  description = "S3 Bucket Name for Project Artifacts"
}

output "s3_artifacts_bucket_arn" {
  value       = aws_s3_bucket.artifacts.arn
  description = "S3 Bucket ARN"
}

output "cloudwatch_log_group" {
  value       = aws_cloudwatch_log_group.worker_logs.name
  description = "CloudWatch Log Group Name"
}
