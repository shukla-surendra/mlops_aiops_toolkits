variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Name prefix / tag."
  type        = string
  default     = "aws-mastery-efs"
}

variable "one_zone" {
  description = "true = One Zone storage class (single AZ, ~half cost). false = Standard (multi-AZ, resilient)."
  type        = bool
  default     = false
}

variable "throughput_mode" {
  description = "elastic (recommended, pay-per-use) | bursting | provisioned."
  type        = string
  default     = "elastic"
}

variable "provisioned_throughput_mibps" {
  description = "Only used when throughput_mode = provisioned."
  type        = number
  default     = 0
}

variable "transition_to_ia" {
  description = "Lifecycle: move files to Infrequent Access after this idle period (or empty to disable)."
  type        = string
  default     = "AFTER_30_DAYS"
}

variable "client_cidr" {
  description = "CIDR allowed to reach NFS 2049. Defaults to the VPC CIDR (in real use, reference a client SG instead)."
  type        = string
  default     = ""
}
