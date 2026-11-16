environment          = "staging"
aws_region           = "us-east-1"
vpc_cidr             = "10.1.0.0/16"
fargate_cpu          = 2048 # 2 vCPU
fargate_memory       = 4096 # 4 GB
desired_worker_count = 1
max_worker_count     = 3
monthly_budget_usd   = 75
