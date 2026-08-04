##############################################################################
# Locals — naming, tagging, and the computed subnet CIDRs.
##############################################################################
locals {
  name = "${var.project}-${var.environment}"

  tags = merge(
    {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
      Module      = "aws/terraform/vpc"
    },
    var.extra_tags,
  )

  # cidrsubnet(prefix, newbits, netnum): carve /24s out of the /16 (newbits = 8).
  # Tier layout mirrors docs/vpc/networking.md §5:
  #   public = .0,.1,.2   app = .10,.11,.12   data = .20,.21,.22
  public_subnets = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 8, i)]
  app_subnets    = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 8, i + 10)]
  data_subnets   = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 8, i + 20)]

  # How many NAT GWs to create, and which one each AZ's app subnet routes through.
  nat_count = var.single_nat_gateway ? 1 : length(var.azs)
}

##############################################################################
# VPC + Internet Gateway
##############################################################################
resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr

  # Both must be true for the Route 53 Resolver (base+2) and private DNS on
  # endpoints to work. This is a classic silent gotcha — see networking.md §4.
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = local.name }
}

# The IGW is horizontally scaled + free; you pay only for data transfer.
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${local.name}-igw" }
}

##############################################################################
# Subnets — one public / app / data per AZ (count fans out over var.azs)
##############################################################################
resource "aws_subnet" "public" {
  count                   = length(var.azs)
  vpc_id                  = aws_vpc.this.id
  availability_zone       = var.azs[count.index]
  cidr_block              = local.public_subnets[count.index]
  map_public_ip_on_launch = true # instances here get a public IP automatically

  tags = {
    Name = "${local.name}-public-${var.azs[count.index]}"
    Tier = "public"
  }
}

resource "aws_subnet" "app" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.this.id
  availability_zone = var.azs[count.index]
  cidr_block        = local.app_subnets[count.index]

  tags = {
    Name = "${local.name}-app-${var.azs[count.index]}"
    Tier = "app"
  }
}

resource "aws_subnet" "data" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.this.id
  availability_zone = var.azs[count.index]
  cidr_block        = local.data_subnets[count.index]

  tags = {
    Name = "${local.name}-data-${var.azs[count.index]}"
    Tier = "data"
  }
}

##############################################################################
# NAT Gateways (+ their Elastic IPs) — live in the PUBLIC subnets
##############################################################################
resource "aws_eip" "nat" {
  count  = local.nat_count
  domain = "vpc"
  tags   = { Name = "${local.name}-nat-eip-${count.index}" }
}

resource "aws_nat_gateway" "this" {
  count         = local.nat_count
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id # NAT GW sits in a public subnet
  depends_on    = [aws_internet_gateway.this]       # needs the IGW to reach the internet

  tags = { Name = "${local.name}-nat-${count.index}" }
}

##############################################################################
# Route tables
#   public : shared, default route → IGW  ("public subnet" = this route exists)
#   app    : one per AZ, default route → that AZ's NAT GW (or the single one)
#   data   : one per AZ, LOCAL ONLY — no 0.0.0.0/0, so it cannot touch the internet
##############################################################################

# --- Public ---
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${local.name}-public-rt" }
}

resource "aws_route" "public_default" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- App (private, with egress) ---
resource "aws_route_table" "app" {
  count  = length(var.azs)
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${local.name}-app-rt-${var.azs[count.index]}" }
}

resource "aws_route" "app_default" {
  count                  = length(var.azs)
  route_table_id         = aws_route_table.app[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  # If single NAT, everyone uses index 0; else each AZ uses its own NAT GW.
  nat_gateway_id = aws_nat_gateway.this[var.single_nat_gateway ? 0 : count.index].id
}

resource "aws_route_table_association" "app" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.app[count.index].id
  route_table_id = aws_route_table.app[count.index].id
}

# --- Data (private, NO egress) ---
resource "aws_route_table" "data" {
  count  = length(var.azs)
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${local.name}-data-rt-${var.azs[count.index]}" }
  # Intentionally NO 0.0.0.0/0 route. Only the immutable `local` route exists,
  # so this tier is unreachable from / cannot reach the internet by design.
}

resource "aws_route_table_association" "data" {
  count          = length(var.azs)
  subnet_id      = aws_subnet.data[count.index].id
  route_table_id = aws_route_table.data[count.index].id
}
