##############################################################################
# Locals
##############################################################################
locals {
  name = var.project
  tags = {
    Project   = var.project
    ManagedBy = "terraform"
    Module    = "aws/terraform/sagemaker"
  }
}

##############################################################################
# Execution role — what the endpoint's containers can do (LEAST PRIVILEGE)
# The container runs arbitrary code; scope this tightly in production.
##############################################################################
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "exec" {
  name               = "${local.name}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

# NOTE: AmazonSageMakerFullAccess is broad — fine for a demo, NOT for prod.
# In production replace with a policy scoped to the specific S3 bucket(s),
# the ECR repo, KMS key, and CloudWatch log group.
resource "aws_iam_role_policy_attachment" "exec" {
  role       = aws_iam_role.exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

##############################################################################
# Model = container image + trained artifact + role
##############################################################################
resource "aws_sagemaker_model" "this" {
  name               = "${local.name}-model"
  execution_role_arn = aws_iam_role.exec.arn

  primary_container {
    image          = var.container_image
    model_data_url = var.model_data_url
  }

  tags = { Name = "${local.name}-model" }
}

##############################################################################
# Endpoint configuration = instance type/count + production variant(s)
##############################################################################
resource "aws_sagemaker_endpoint_configuration" "this" {
  name = "${local.name}-epc"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.this.name
    initial_instance_count = var.min_capacity
    instance_type          = var.instance_type
    initial_variant_weight = 1.0
  }

  # Capture inputs/outputs to S3 for Model Monitor (commented — set a bucket to enable):
  # data_capture_config {
  #   initial_sampling_percentage = 20
  #   destination_s3_uri          = "s3://your-bucket/datacapture"
  #   capture_options { capture_mode = "Input" }
  #   capture_options { capture_mode = "Output" }
  # }

  tags = { Name = "${local.name}-epc" }
}

##############################################################################
# Endpoint = the persistent serving fleet (bills while running!)
##############################################################################
resource "aws_sagemaker_endpoint" "this" {
  name                 = "${local.name}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.this.name
  tags                 = { Name = "${local.name}-endpoint" }
}

##############################################################################
# Autoscaling on invocations-per-instance (target tracking)
##############################################################################
resource "aws_appautoscaling_target" "ep" {
  service_namespace  = "sagemaker"
  resource_id        = "endpoint/${aws_sagemaker_endpoint.this.name}/variant/AllTraffic"
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  min_capacity       = var.min_capacity
  max_capacity       = var.max_capacity
}

resource "aws_appautoscaling_policy" "ep" {
  name               = "${local.name}-scale-invocations"
  policy_type        = "TargetTrackingScaling"
  service_namespace  = aws_appautoscaling_target.ep.service_namespace
  resource_id        = aws_appautoscaling_target.ep.resource_id
  scalable_dimension = aws_appautoscaling_target.ep.scalable_dimension

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "SageMakerVariantInvocationsPerInstance"
    }
    target_value       = var.invocations_target_per_instance
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
