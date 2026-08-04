output "file_system_id" {
  value       = aws_efs_file_system.this.id
  description = "EFS filesystem ID."
}

output "file_system_dns" {
  value       = "${aws_efs_file_system.this.id}.efs.${var.region}.amazonaws.com"
  description = "DNS name to mount (resolves to the AZ-local mount target inside the VPC)."
}

output "access_point_id" {
  value       = aws_efs_access_point.app.id
  description = "Access Point pinning uid/gid 1001 to /app."
}

output "mount_target_ids" {
  value       = [for m in aws_efs_mount_target.this : m.id]
  description = "Mount target ENIs (one per AZ, or one for One Zone)."
}

output "security_group_id" {
  value       = aws_security_group.efs.id
  description = "SG on the mount targets (allows NFS 2049 from clients)."
}

output "mount_command" {
  value = <<-EOT
    # On a client in this VPC (install amazon-efs-utils first):
    sudo yum install -y amazon-efs-utils        # or: apt-get install amazon-efs-utils
    sudo mkdir -p /mnt/efs

    # Mount the root with in-transit TLS (required by the filesystem policy):
    sudo mount -t efs -o tls ${aws_efs_file_system.this.id}:/ /mnt/efs

    # Or mount through the Access Point (pinned to /app as uid 1001):
    sudo mount -t efs -o tls,accesspoint=${aws_efs_access_point.app.id} ${aws_efs_file_system.this.id}:/ /mnt/efs

    # NOTE: the client instance's SG must be allowed by ${aws_security_group.efs.id} (NFS 2049).
  EOT
  description = "Copy-paste mount instructions."
}
