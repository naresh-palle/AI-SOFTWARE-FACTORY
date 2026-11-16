environment          = "prod"
aws_region           = "us-east-1"
vpc_cidr             = "10.2.0.0/16"
fargate_cpu          = 2048 # 2 vCPU
fargate_memory       = 4096 # 4 GB
desired_worker_count = 2
max_worker_count     = 10
monthly_budget_usd   = 250
