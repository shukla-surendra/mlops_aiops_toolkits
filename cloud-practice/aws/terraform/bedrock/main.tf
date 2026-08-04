##############################################################################
# Locals + account context
##############################################################################
locals {
  name = var.project
  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Module    = "aws/terraform/bedrock"
  }
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

##############################################################################
# App IAM role — least privilege: invoke ONLY the allowed model ARNs
# (Scoping to cheap models is a genuine cost control — see best-practices.md.)
##############################################################################
data "aws_iam_policy_document" "app_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"] # swap for your app's principal (Lambda/ECS/…)
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${local.name}-app-role"
  assume_role_policy = data.aws_iam_policy_document.app_assume.json
}

data "aws_iam_policy_document" "invoke" {
  statement {
    sid = "InvokeAllowedModels"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
      "bedrock:Converse",
      "bedrock:ConverseStream",
    ]
    resources = var.allowed_model_arns
  }
  # Allow applying the guardrail (if created).
  dynamic "statement" {
    for_each = var.enable_guardrail ? [1] : []
    content {
      sid       = "ApplyGuardrail"
      actions   = ["bedrock:ApplyGuardrail"]
      resources = [aws_bedrock_guardrail.this[0].guardrail_arn]
    }
  }
}

resource "aws_iam_role_policy" "invoke" {
  name   = "${local.name}-invoke"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.invoke.json
}

##############################################################################
# Guardrail — content filters + PII redaction (attach on every prod invocation)
##############################################################################
resource "aws_bedrock_guardrail" "this" {
  count                     = var.enable_guardrail ? 1 : 0
  name                      = "${local.name}-guardrail"
  blocked_input_messaging   = "Your request was blocked by content policy."
  blocked_outputs_messaging = "The response was blocked by content policy."
  description               = "Demo guardrail: content filters + PII redaction."

  content_policy_config {
    dynamic "filters_config" {
      for_each = toset(["HATE", "INSULTS", "SEXUAL", "VIOLENCE", "MISCONDUCT", "PROMPT_ATTACK"])
      content {
        type            = filters_config.value
        input_strength  = "HIGH"
        # PROMPT_ATTACK output filtering must be NONE (input-only category).
        output_strength = filters_config.value == "PROMPT_ATTACK" ? "NONE" : "HIGH"
      }
    }
  }

  sensitive_information_policy_config {
    dynamic "pii_entities_config" {
      for_each = toset(["EMAIL", "PHONE", "CREDIT_DEBIT_CARD_NUMBER", "US_SOCIAL_SECURITY_NUMBER"])
      content {
        type   = pii_entities_config.value
        action = "ANONYMIZE" # redact rather than block
      }
    }
  }

  tags = { Name = "${local.name}-guardrail" }
}

##############################################################################
# Model invocation logging → S3 (audit trail of prompts/responses)
##############################################################################
resource "aws_s3_bucket" "logs" {
  count         = var.enable_invocation_logging ? 1 : 0
  bucket        = "${local.name}-invocation-logs-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

# Bedrock service must be allowed to write logs into the bucket.
data "aws_iam_policy_document" "logs_bucket" {
  count = var.enable_invocation_logging ? 1 : 0
  statement {
    sid       = "AllowBedrockPutLogs"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.logs[0].arn}/*"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "logs" {
  count  = var.enable_invocation_logging ? 1 : 0
  bucket = aws_s3_bucket.logs[0].id
  policy = data.aws_iam_policy_document.logs_bucket[0].json
}

resource "aws_bedrock_model_invocation_logging_configuration" "this" {
  count      = var.enable_invocation_logging ? 1 : 0
  depends_on = [aws_s3_bucket_policy.logs]

  logging_config {
    embedding_data_delivery_enabled = true
    image_data_delivery_enabled     = false
    text_data_delivery_enabled      = true

    s3_config {
      bucket_name = aws_s3_bucket.logs[0].id
      key_prefix  = "bedrock-logs"
    }
  }
}
