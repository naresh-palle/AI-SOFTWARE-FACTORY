environment          = "dev"
aws_region           = "us-east-1"
vpc_cidr             = "10.0.0.0/16"
fargate_cpu          = 1024 # 1 vCPU
fargate_memory       = 2048 # 2 GB
desired_worker_count = 1
max_worker_count     = 2
monthly_budget_usd   = 35
