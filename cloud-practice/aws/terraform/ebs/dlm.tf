##############################################################################
# Data Lifecycle Manager (DLM) — automated, tag-driven snapshot backups.
# This is the production-standard way to back up EBS (vs hand-rolled cron).
# It snapshots every volume tagged Backup=true daily and keeps the last 7.
##############################################################################

# DLM needs a service role it can assume to create/delete snapshots.
resource "aws_iam_role" "dlm" {
  count = var.enable_dlm_backups ? 1 : 0
  name  = "${local.name}-dlm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "dlm.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# AWS-managed policy with exactly the snapshot permissions DLM needs.
resource "aws_iam_role_policy_attachment" "dlm" {
  count      = var.enable_dlm_backups ? 1 : 0
  role       = aws_iam_role.dlm[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSDataLifecycleManagerServiceRole"
}

resource "aws_dlm_lifecycle_policy" "daily" {
  count              = var.enable_dlm_backups ? 1 : 0
  description        = "${local.name} daily EBS snapshots (Backup=true), keep 7"
  execution_role_arn = aws_iam_role.dlm[0].arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    # Which volumes to back up: those tagged Backup=true.
    target_tags = {
      Backup = "true"
    }

    schedule {
      name = "daily-0300-utc"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 7 # keep the last 7 snapshots per volume
      }

      # Tag snapshots so they're findable/attributable.
      tags_to_add = {
        SnapshotCreator = "dlm"
        Project         = var.project
      }

      copy_tags = true # copy the source volume's tags onto the snapshot
    }
  }
}
