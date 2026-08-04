output "app_role_arn" {
  value       = aws_iam_role.app.arn
  description = "IAM role scoped to invoke only the allowed model ARNs."
}

output "allowed_model_arns" {
  value       = var.allowed_model_arns
  description = "Models this role may invoke."
}

output "guardrail_id" {
  value       = try(aws_bedrock_guardrail.this[0].guardrail_id, null)
  description = "Guardrail ID (pass to Converse/InvokeModel as guardrailIdentifier)."
}

output "guardrail_version" {
  value       = try(aws_bedrock_guardrail.this[0].version, null)
  description = "Guardrail version (use DRAFT during dev, or a published version)."
}

output "invocation_logs_bucket" {
  value       = try(aws_s3_bucket.logs[0].id, null)
  description = "S3 bucket capturing model invocation logs (null if disabled)."
}

output "next_steps" {
  value = <<-EOT
    Enable model access first: Bedrock console → Model access → enable the family you plan to call.
    Then, from a principal that can assume ${aws_iam_role.app.arn}:
      aws bedrock-runtime converse \
        --model-id anthropic.claude-haiku-4-5 \
        --messages '[{"role":"user","content":[{"text":"Say hi in 5 words"}]}]' \
        ${var.enable_guardrail ? "--guardrail-config guardrailIdentifier=<id>,guardrailVersion=DRAFT" : ""}
    See ../../boto3/bedrock for a Python version.
  EOT
}
