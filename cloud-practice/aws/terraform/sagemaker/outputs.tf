output "endpoint_name" {
  value       = aws_sagemaker_endpoint.this.name
  description = "Invoke with sagemaker-runtime InvokeEndpoint (this endpoint bills while it exists — destroy when done)."
}

output "model_name" {
  value = aws_sagemaker_model.this.name
}

output "execution_role_arn" {
  value = aws_iam_role.exec.arn
}

output "invoke_example" {
  value = <<-EOT
    aws sagemaker-runtime invoke-endpoint \
      --endpoint-name ${aws_sagemaker_endpoint.this.name} \
      --content-type text/csv \
      --body "5.1,3.5,1.4,0.2" \
      /dev/stdout
    # (content-type + body format depend on YOUR model's serving container.)
  EOT
}
