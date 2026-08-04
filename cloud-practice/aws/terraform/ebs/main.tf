##############################################################################
# Locals + lookups
##############################################################################
locals {
  name = var.project
  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Module    = "aws/terraform/ebs"
  }
}

# Use the default VPC + a default subnet in the chosen AZ (keeps this example
# self-contained; in real life you'd reference the VPC module's outputs).
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "in_az" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
  filter {
    name   = "availability-zone"
    values = [var.availability_zone]
  }
}

# Latest Amazon Linux 2023 AMI via the public SSM parameter (no hardcoded AMI IDs).
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

##############################################################################
# KMS key for EBS encryption (customer-managed → shareable, auditable)
##############################################################################
resource "aws_kms_key" "ebs" {
  description             = "${local.name} EBS encryption key"
  deletion_window_in_days = 7      # a KMS key is data-lifecycle: deleting it destroys the data
  enable_key_rotation     = true
}

resource "aws_kms_alias" "ebs" {
  name          = "alias/${local.name}-ebs"
  target_key_id = aws_kms_key.ebs.key_id
}

##############################################################################
# EC2 instance to attach volumes to
##############################################################################
resource "aws_instance" "demo" {
  ami               = data.aws_ssm_parameter.al2023.value
  instance_type     = var.instance_type
  availability_zone = var.availability_zone
  subnet_id         = data.aws_subnets.in_az.ids[0]

  # Encrypt the ROOT volume too (best practice). gp3 root.
  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
    kms_key_id  = aws_kms_key.ebs.arn
  }

  tags = { Name = "${local.name}-demo" }
}

##############################################################################
# gp3 data volume (the default choice) — attached as a secondary device
##############################################################################
resource "aws_ebs_volume" "gp3" {
  availability_zone = var.availability_zone # MUST match the instance's AZ
  size              = var.gp3_size_gib
  type              = "gp3"
  iops              = var.gp3_iops       # baseline 3000 free
  throughput        = var.gp3_throughput # baseline 125 MB/s free
  encrypted         = true
  kms_key_id        = aws_kms_key.ebs.arn

  tags = {
    Name   = "${local.name}-gp3-data"
    Backup = "true" # DLM targets this tag (see dlm.tf)
  }
}

resource "aws_volume_attachment" "gp3" {
  device_name = "/dev/sdf" # Nitro guests may surface this as /dev/nvme1n1
  volume_id   = aws_ebs_volume.gp3.id
  instance_id = aws_instance.demo.id
}

##############################################################################
# Optional io2 high-performance volume (provisioned IOPS — costs more)
##############################################################################
resource "aws_ebs_volume" "io2" {
  count             = var.create_io2 ? 1 : 0
  availability_zone = var.availability_zone
  size              = var.io2_size_gib
  type              = "io2"
  iops              = var.io2_iops
  encrypted         = true
  kms_key_id        = aws_kms_key.ebs.arn

  tags = {
    Name   = "${local.name}-io2-data"
    Backup = "true"
  }
}

resource "aws_volume_attachment" "io2" {
  count       = var.create_io2 ? 1 : 0
  device_name = "/dev/sdg"
  volume_id   = aws_ebs_volume.io2[0].id
  instance_id = aws_instance.demo.id
}
