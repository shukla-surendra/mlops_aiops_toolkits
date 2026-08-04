##############################################################################
# Locals + lookups (self-contained: uses the default VPC + its subnets)
##############################################################################
locals {
  name = var.project
  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Module    = "aws/terraform/efs"
  }
}

data "aws_vpc" "default" {
  default = true
}

data "aws_availability_zones" "available" {
  state = "available"
}

# One subnet per AZ in the default VPC (default VPCs have exactly one subnet/AZ).
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# For One Zone, pin the filesystem + its single mount target to one AZ.
locals {
  one_zone_az   = var.one_zone ? data.aws_availability_zones.available.names[0] : null
  client_cidr   = var.client_cidr != "" ? var.client_cidr : data.aws_vpc.default.cidr_block
  # Standard: a mount target per default subnet (≈ one per AZ). One Zone: just the AZ's subnet.
  mount_subnets = var.one_zone ? [data.aws_subnets.in_az[0].ids[0]] : data.aws_subnets.default.ids
}

# Only needed for One Zone: find a subnet in the chosen AZ.
data "aws_subnets" "in_az" {
  count = var.one_zone ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "availability-zone"
    values = [local.one_zone_az]
  }
}

##############################################################################
# Security Group for the mount targets — allow NFS 2049 from clients only
##############################################################################
resource "aws_security_group" "efs" {
  name        = "${local.name}-efs-sg"
  description = "EFS mount target: allow NFS 2049 from clients"
  vpc_id      = data.aws_vpc.default.id
  tags        = { Name = "${local.name}-efs-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "nfs" {
  security_group_id = aws_security_group.efs.id
  description       = "NFS from clients (use a client SG reference in production, not a CIDR)"
  cidr_ipv4         = local.client_cidr
  from_port         = 2049
  to_port           = 2049
  ip_protocol       = "tcp"
}

##############################################################################
# The EFS filesystem (encrypted, lifecycle tiering, chosen throughput mode)
##############################################################################
resource "aws_efs_file_system" "this" {
  creation_token  = local.name
  encrypted       = true # KMS at rest (uses the default EFS key unless kms_key_id set)
  throughput_mode = var.throughput_mode
  provisioned_throughput_in_mibps = (
    var.throughput_mode == "provisioned" ? var.provisioned_throughput_mibps : null
  )

  # One Zone if set; null = Standard (multi-AZ).
  availability_zone_name = local.one_zone_az

  # Tier cold files to Infrequent Access to save cost.
  dynamic "lifecycle_policy" {
    for_each = var.transition_to_ia != "" ? [1] : []
    content {
      transition_to_ia = var.transition_to_ia
    }
  }

  tags = { Name = local.name }
}

##############################################################################
# Mount targets — one ENI per AZ (or one for One Zone)
##############################################################################
resource "aws_efs_mount_target" "this" {
  for_each        = toset(local.mount_subnets)
  file_system_id  = aws_efs_file_system.this.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

##############################################################################
# Access Point — pins a POSIX identity + root dir (per-app/tenant isolation)
##############################################################################
resource "aws_efs_access_point" "app" {
  file_system_id = aws_efs_file_system.this.id

  posix_user {
    uid = 1001
    gid = 1001
  }

  root_directory {
    path = "/app"
    creation_info {
      owner_uid   = 1001
      owner_gid   = 1001
      permissions = "0755"
    }
  }

  tags = { Name = "${local.name}-ap-app" }
}

##############################################################################
# Filesystem policy — refuse any mount that isn't using TLS (in-transit encryption)
##############################################################################
resource "aws_efs_file_system_policy" "require_tls" {
  file_system_id = aws_efs_file_system.this.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyNonTLS"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = "*"
      Resource  = aws_efs_file_system.this.arn
      Condition = {
        Bool = { "aws:SecureTransport" = "false" }
      }
    }]
  })
}
