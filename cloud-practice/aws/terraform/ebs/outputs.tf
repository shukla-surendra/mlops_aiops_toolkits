output "instance_id" {
  value       = aws_instance.demo.id
  description = "EC2 instance the volumes attach to (connect via SSM Session Manager)."
}

output "availability_zone" {
  value       = var.availability_zone
  description = "AZ shared by the instance and volumes."
}

output "kms_key_arn" {
  value       = aws_kms_key.ebs.arn
  description = "Customer-managed KMS key encrypting the volumes."
}

output "gp3_volume_id" {
  value       = aws_ebs_volume.gp3.id
  description = "The gp3 data volume."
}

output "io2_volume_id" {
  value       = try(aws_ebs_volume.io2[0].id, null)
  description = "The io2 volume (null unless create_io2 = true)."
}

output "dlm_policy_id" {
  value       = try(aws_dlm_lifecycle_policy.daily[0].id, null)
  description = "DLM backup policy ID (null if disabled)."
}

output "next_steps" {
  value = <<-EOT
    1. Connect: Session Manager to ${aws_instance.demo.id} (no SSH needed; instance needs the SSM role/agent — AL2023 has the agent).
    2. Find the disk:   lsblk           (the gp3 volume shows as /dev/nvme1n1 on Nitro)
    3. Format + mount:  sudo mkfs -t xfs /dev/nvme1n1 && sudo mkdir /data && sudo mount /dev/nvme1n1 /data
    4. Persist test:    echo hello | sudo tee /data/test.txt
    5. Snapshot:        aws ec2 create-snapshot --volume-id ${aws_ebs_volume.gp3.id}
    6. Resize demo:     aws ec2 modify-volume --volume-id ${aws_ebs_volume.gp3.id} --size 40
                        then in guest: sudo xfs_growfs /data
    NOTE: to actually use SSM you must attach an instance profile with AmazonSSMManagedInstanceCore
          (left out to keep this module minimal — add it or use EC2 Instance Connect).
  EOT
}
