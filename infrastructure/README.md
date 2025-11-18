# CloudCostly Infrastructure

Terraform configuration for deploying CloudCostly to AWS.

## Architecture

- **VPC**: Custom VPC with public and private subnets across 2 AZs
- **RDS**: PostgreSQL database in private subnets
- **Lambda**: Python API handlers
- **API Gateway**: HTTP API for REST endpoints
- **S3**: Buckets for Cost and Usage Reports and frontend hosting
- **IAM**: Roles and policies for cross-account access

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured
- AWS account with appropriate permissions

## Setup

1. Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. Edit `terraform.tfvars` with your values:
```hcl
db_username = "your_username"
db_password = "your_secure_password"
```

3. Initialize Terraform:
```bash
terraform init
```

4. Review the plan:
```bash
terraform plan
```

5. Apply the configuration:
```bash
terraform apply
```

## Outputs

After applying, Terraform will output:
- API Gateway URL
- Database endpoint
- S3 bucket names
- Frontend website URL

## State Management

For production, configure S3 backend in `main.tf`:

```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "cloudcostly/terraform.tfstate"
  region         = "us-east-1"
  dynamodb_table = "terraform-locks"
  encrypt        = true
}
```

## Cost Estimation

Development environment (estimated monthly):
- RDS t3.micro: ~$15
- Lambda: Pay per use (~$5-20 depending on traffic)
- API Gateway: Pay per request (~$5-10)
- NAT Gateway: ~$32
- **Total: ~$60-80/month**

Production environment would scale costs based on:
- Larger RDS instances
- More Lambda executions
- Higher API Gateway traffic
- Additional CloudWatch logs

## Security Notes

- Never commit `terraform.tfvars` with real credentials
- Use AWS Secrets Manager for sensitive data in production
- Review security groups before deploying to production
- Enable CloudTrail for audit logging
- Set up proper CORS origins for API Gateway
