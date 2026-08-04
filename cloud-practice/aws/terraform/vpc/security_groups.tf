##############################################################################
# Example tiered Security Groups.
#
# The teaching point: chain SGs by REFERENCING each other, not by hardcoding
# CIDRs. "app_sg allows 8080 from alb_sg" means "from whatever ENIs are in the
# ALB SG" — it auto-tracks scaling. This is the idiom the docs call a distributed,
# stateful, per-ENI firewall (architecture.md §3c). SGs are STATEFUL: allow the
# inbound and the return traffic is automatically permitted (no egress rule needed
# for replies).
##############################################################################

# --- Public tier: internet-facing load balancer ---
resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "Public ALB: allow 80/443 from the internet"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-alb-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from internet"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS from internet"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_all_out" {
  security_group_id = aws_security_group.alb.id
  description       = "Allow all egress (to app tier)"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# --- App tier: only reachable FROM the ALB SG ---
resource "aws_security_group" "app" {
  name        = "${local.name}-app-sg"
  description = "App tier: allow 8080 only from the ALB SG"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-app-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  description                  = "App port from ALB SG (referenced, not CIDR)"
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = 8080
  to_port                      = 8080
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "app_all_out" {
  security_group_id = aws_security_group.app.id
  description       = "Egress for updates/S3/etc. (via NAT or endpoints)"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# --- Data tier: only reachable FROM the app SG, e.g. Postgres 5432 ---
resource "aws_security_group" "data" {
  name        = "${local.name}-data-sg"
  description = "Data tier: allow 5432 only from the app SG"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-data-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "data_from_app" {
  security_group_id            = aws_security_group.data.id
  description                  = "Postgres from app SG"
  referenced_security_group_id = aws_security_group.app.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}

# Deliberately NO broad egress rule on the data tier: combined with the
# egress-less data route table, this box is sealed. Add narrow rules if it
# needs to reach, say, an S3 gateway endpoint for backups.
