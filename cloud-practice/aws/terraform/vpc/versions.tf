# Provider + Terraform version pinning.
# Pin these in real projects — a surprise provider major version can rewrite your plan.
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  # default_tags applies these to every taggable resource the provider creates.
  # Consistent tagging is how you later attribute cost (Cost Allocation Tags) and
  # find blast radius during an incident. See docs/vpc/best-practices.md (later module).
  default_tags {
    tags = local.tags
  }
}
