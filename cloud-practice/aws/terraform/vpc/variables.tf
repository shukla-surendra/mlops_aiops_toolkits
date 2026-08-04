variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short name used to prefix/namespace resources and tags."
  type        = string
  default     = "aws-mastery-vpc"
}

variable "environment" {
  description = "Environment name (dev/staging/prod). Used in tags."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Primary CIDR for the VPC. /16 gives room for 256 /24 subnets."
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = <<-EOT
    Availability Zones to spread across. TWO is the minimum for HA; THREE is the
    prod default (survives an AZ loss while keeping quorum for 3-node systems).
    Each AZ gets one public + one app + one data subnet.
  EOT
  type    = list(string)
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "single_nat_gateway" {
  description = <<-EOT
    true  = ONE NAT Gateway shared by all AZs (cheaper, but a single-AZ egress
            failure domain AND cross-AZ data-processing charges). Fine for dev.
    false = ONE NAT Gateway PER AZ (prod default: no cross-AZ egress $, survives
            an AZ outage). NAT GWs are the #1 hidden cost — choose deliberately.
  EOT
  type    = bool
  default = true
}

variable "enable_s3_gateway_endpoint" {
  description = "Create a free S3 Gateway Endpoint so S3 traffic bypasses the NAT GW (and its per-GB charge)."
  type        = bool
  default     = true
}

variable "extra_tags" {
  description = "Additional tags merged into the default tag set."
  type        = map(string)
  default     = {}
}
