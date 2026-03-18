# EC2 PowerBI Desktop - remote access via SSM port forwarding
output "ec2_powerbi_key_name" {
  value       = length(aws_instance.powerbi_desktop) > 0 ? var.ec2_key_name : null
  description = "Key pair name - use your private key to decrypt the Windows Administrator password"
}

output "ec2_powerbi_instance_id" {
  value       = length(aws_instance.powerbi_desktop) > 0 ? aws_instance.powerbi_desktop[0].id : null
  description = "Instance ID for SSM port forwarding"
}

output "ec2_rdp_port_forward_command" {
  value       = length(aws_instance.powerbi_desktop) > 0 ? "aws ssm start-session --target ${aws_instance.powerbi_desktop[0].id} --document-name AWS-StartPortForwardingSession --parameters portNumber=3389,localPortNumber=3389" : null
  description = "Run this to forward RDP (3389) to localhost, then RDP to localhost:3389"
}
