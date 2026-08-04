variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "availability_zone" {
  description = "AZ for the instance AND its volumes (EBS attaches only within one AZ)."
  type        = string
  default     = "us-east-1a"
}

variable "project" {
  description = "Name prefix / tag."
  type        = string
  default     = "aws-mastery-ebs"
}

variable "instance_type" {
  description = "Small instance is enough to demo attach/format/snapshot."
  type        = string
  default     = "t3.micro"
}

variable "gp3_size_gib" {
  description = "Size of the general-purpose gp3 data volume."
  type        = number
  default     = 20
}

variable "gp3_iops" {
  description = "Provisioned IOPS for gp3 (baseline 3000 free; up to 16000)."
  type        = number
  default     = 3000
}

variable "gp3_throughput" {
  description = "Provisioned throughput MB/s for gp3 (baseline 125 free; up to 1000)."
  type        = number
  default     = 125
}

variable "create_io2" {
  description = "Also create a high-performance io2 volume (costs more — provisioned IOPS)."
  type        = bool
  default     = false
}

variable "io2_size_gib" {
  type    = number
  default = 20
}

variable "io2_iops" {
  description = "Provisioned IOPS for io2 (ratio up to 500:1 for io2; higher for Block Express)."
  type        = number
  default     = 3000
}

variable "enable_dlm_backups" {
  description = "Create a Data Lifecycle Manager policy that snapshots volumes tagged Backup=true daily."
  type        = bool
  default     = true
}
