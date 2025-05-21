output "resource_group_name" {
  description = "Name of the Azure Resource Group used"
  value       = azurerm_resource_group.main.name
}

output "vm_public_ip" {
  description = "Public IP address of the deployed Virtual Machine"
  value       = azurerm_public_ip.vm_pip.ip_address
}

output "vm_admin_username" {
  description = "Admin username for the Virtual Machine"
  value       = var.vm_admin_username
}

output "ssh_to_vm_command" {
  description = "Command to SSH into the Virtual Machine"
  value       = "ssh ${var.vm_admin_username}@${azurerm_public_ip.vm_pip.ip_address}"
}

output "application_url" {
  description = "URL to access the deployed application"
  value       = "http://${azurerm_public_ip.vm_pip.ip_address}:${var.app_host_port}"
}

output "postgresql_server_fqdn" {
  description = "Fully Qualified Domain Name (FQDN) of the Azure PostgreSQL Flexible Server"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgresql_server_name" {
  description = "Name of the Azure PostgreSQL Flexible Server instance"
  value       = azurerm_postgresql_flexible_server.main.name
}

output "postgresql_default_database_name_suggestion" {
  description = "Default database name (often 'postgres' or server name) to connect to for PostgreSQL"
  value       = "postgres (or the server name if it creates an initial DB with that name)"
}

output "acr_login_server_used" {
  description = "Login server of the Azure Container Registry that was referenced"
  value       = azurerm_container_registry.main.login_server
}

output "custom_data_troubleshooting_tip" {
  description = "If app not running, SSH to VM and check /var/log/cloud-init-output.log and docker logs"
  value       = "Check /var/log/cloud-init-output.log on VM for errors. Also check 'sudo docker ps -a' and 'sudo docker logs <container_id>'."
}