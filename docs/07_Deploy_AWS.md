# 07 – One‑click AWS deploy

1. `terraform init && terraform apply` inside `infra/`  
   * Creates VPC, RDS Postgres, EKS cluster, ElastiCache Redis.  
2. `make bootstrap`  
   * Pushes Docker images to ECR, seeds Parameter Store secrets.  
3. Route 53 CNAME `api.YOURDOMAIN.ai` → ALB output.

**Scaling**: ECS Fargate `cpu=0.25` → `provider: FARGATE_SPOT` with auto‑pause (saves ~70 % idle).  
**Monitoring**: AWS CloudWatch + Grafana Cloud Free tier.
