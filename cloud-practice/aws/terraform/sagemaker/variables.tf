variable "region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Name prefix / tag."
  type        = string
  default     = "aws-mastery-sm"
}

variable "container_image" {
  description = <<-EOT
    ECR URI of the serving container. Get one from a training job output, JumpStart,
    or an AWS Deep Learning Container. Example (XGBoost, us-east-1):
    683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1
    (account ID varies by Region — see the SageMaker built-in algorithm docs.)
  EOT
  type    = string
}

variable "model_data_url" {
  description = "S3 URI of the trained model artifact (model.tar.gz). Produced by a training job."
  type        = string
}

variable "instance_type" {
  description = "Serving instance type."
  type        = string
  default     = "ml.m5.large"
}

variable "min_capacity" {
  description = "Autoscaling minimum instances."
  type        = number
  default     = 1
}

variable "max_capacity" {
  description = "Autoscaling maximum instances."
  type        = number
  default     = 3
}

variable "invocations_target_per_instance" {
  description = "Target-tracking autoscaling: invocations/min/instance to hold."
  type        = number
  default     = 1000
}
