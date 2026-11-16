variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for deployment"
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  default     = "ai-software-factory"
  description = "Project name tag and identifier prefix"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "fargate_cpu" {
  type        = number
  default     = 2048
  description = "CPU units for worker Fargate task (2 vCPU)"
}

variable "fargate_memory" {
  type        = number
  default     = 4096
  description = "Memory in MB for worker Fargate task (4 GB)"
}

variable "desired_worker_count" {
  type        = number
  default     = 1
  description = "Number of persistent Fargate worker instances"
}

variable "max_worker_count" {
  type        = number
  default     = 5
  description = "Maximum auto-scaling worker limit"
}

variable "monthly_budget_usd" {
  type        = number
  default     = 100
  description = "AWS Budgets monthly limit for cost control"
}
