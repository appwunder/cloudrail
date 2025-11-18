terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure S3 backend for state
    # bucket = "cloudcostly-terraform-state"
    # key    = "prod/terraform.tfstate"
    # region = "us-east-1"
    # dynamodb_table = "cloudcostly-terraform-locks"
    # encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "CloudCostly"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
