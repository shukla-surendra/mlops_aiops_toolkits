output "vpc_id" {
  description = "The VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "The VPC primary CIDR."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs (one per AZ)."
  value       = aws_subnet.public[*].id
}

output "app_subnet_ids" {
  description = "App (private, egress) subnet IDs."
  value       = aws_subnet.app[*].id
}

output "data_subnet_ids" {
  description = "Data (private, no-egress) subnet IDs."
  value       = aws_subnet.data[*].id
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs (1 if single_nat_gateway, else one per AZ)."
  value       = aws_nat_gateway.this[*].id
}

output "nat_public_ips" {
  description = "Elastic IPs of the NAT Gateways (your stable egress IPs — useful for allowlisting)."
  value       = aws_eip.nat[*].public_ip
}

output "s3_gateway_endpoint_id" {
  description = "S3 Gateway Endpoint ID (null if disabled)."
  value       = try(aws_vpc_endpoint.s3[0].id, null)
}

output "security_group_ids" {
  description = "The tiered SG IDs."
  value = {
    alb  = aws_security_group.alb.id
    app  = aws_security_group.app.id
    data = aws_security_group.data.id
  }
}
