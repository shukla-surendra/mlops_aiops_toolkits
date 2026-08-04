variable "region" {
  description = "AWS region (Bedrock model availability varies by Region)."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Name prefix / tag."
  type        = string
  default     = "aws-mastery-bedrock"
}

variable "allowed_model_arns" {
  description = <<-EOT
    Model / inference-profile ARNs the app IAM role may invoke. Scope tightly —
    granting only cheap models is a real cost control. Example (Haiku, us-east-1):
    arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5
    Cross-region profiles look like:
    arn:aws:bedrock:us-east-1:<acct>:inference-profile/us.anthropic.claude-haiku-4-5
  EOT
  type = list(string)
  default = [
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5",
  ]
}

variable "enable_guardrail" {
  description = "Create a Guardrail (content filters + PII redaction)."
  type        = bool
  default     = true
}

variable "enable_invocation_logging" {
  description = "Log model invocations (prompts/responses) to S3 for audit."
  type        = bool
  default     = true
}
