# Least-Privilege IAM Roles & Security Policies for Cloud Worker Infrastructure

# 1. ECS Task Execution Role (ECR pull, CloudWatch logs)
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-${var.environment}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_default" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# 2. Worker Task Role (Runtime permissions for the autonomous worker)
resource "aws_iam_role" "worker_task_role" {
  name = "${var.project_name}-${var.environment}-worker-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Least-privilege inline policy for Worker Task Role
resource "aws_iam_policy" "worker_least_privilege" {
  name        = "${var.project_name}-${var.environment}-worker-policy"
  description = "Scoped access for AI Software Factory Cloud Worker"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Scoped S3 Artifacts Bucket Access
      {
        Sid    = "AllowS3ArtifactAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.artifacts.arn,
          "${aws_s3_bucket.artifacts.arn}/*"
        ]
      },
      # Scoped Secrets Manager Read Access
      {
        Sid    = "AllowSecretsManagerRead"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.project_name}/${var.environment}/*"
        ]
      },
      # CloudWatch Logs PutLogEvents
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.worker_logs.arn}:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_policy_attachment" {
  role       = aws_iam_role.worker_task_role.name
  policy_arn = aws_iam_policy.worker_least_privilege.arn
}
