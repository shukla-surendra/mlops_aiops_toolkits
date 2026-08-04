##############################################################################
# S3 Gateway Endpoint (networking.md §3d)
#
# A Gateway Endpoint is PURELY a route-table entry (a prefix-list target). It
# has NO ENI, NO hourly cost, and NO per-GB cost. It makes S3-bound traffic
# leave via the endpoint instead of the NAT Gateway — often the single biggest
# NAT-bill reduction you can make. We attach it to the app + data route tables.
##############################################################################
resource "aws_vpc_endpoint" "s3" {
  count             = var.enable_s3_gateway_endpoint ? 1 : 0
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"

  # Associate with every private route table so both tiers reach S3 privately.
  route_table_ids = concat(
    aws_route_table.app[*].id,
    aws_route_table.data[*].id,
  )

  tags = { Name = "${local.name}-s3-gw-endpoint" }
}

# NOTE: Interface Endpoints (SQS, KMS, EC2 API, etc.) are aws_vpc_endpoint with
# vpc_endpoint_type = "Interface", subnet_ids, security_group_ids, and
# private_dns_enabled = true. They create ENIs and DO cost per-hour + per-GB.
# We'll add those in a later module (M3/M5) when we wire real workloads.
