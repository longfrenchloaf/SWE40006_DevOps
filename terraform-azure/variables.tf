variable "resource_group_name" {
  description = "Name of the existing Azure Resource Group"
  type        = string
  default     = "MyProjectRGnew" # CHANGE THIS if your RG has a different name
}

variable "location" {
  description = "Azure region where the Resource Group is located and for new resources"
  type        = string
  default     = "Canada Central" # CHANGE THIS to your RG's region
}

variable "project_prefix" {
  description = "A prefix for new resource names for organization"
  type        = string
  default     = "myapp" # e.g., myapp-vnet, myapp-vm
}

variable "vnet_address_space" {
  description = "Address space for the Virtual Network"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "app_subnet_prefix" {
  description = "Address prefix for the application subnet (where VM will be)"
  type        = string
  default     = "10.0.1.0/24"
}

variable "db_subnet_prefix" {
  description = "Address prefix for the database subnet (for PostgreSQL Flexible Server)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "postgresql_admin_login" {
  description = "Admin username for Azure Database for PostgreSQL Flexible Server"
  type        = string
  sensitive   = true
  # No default - Terraform will prompt you for this value
}

variable "postgresql_admin_password" {
  description = "Admin password for Azure Database for PostgreSQL Flexible Server. Must meet complexity requirements."
  type        = string
  sensitive   = true
  # No default - Terraform will prompt you for this value
}

variable "postgresql_sku_name" {
  description = "SKU for PostgreSQL Flexible Server (e.g., B_Standard_B1ms, GP_Standard_D2s_v3)"
  type        = string
  default     = "B_Standard_B1ms" # Burstable, 1 vCore, 2 GiB RAM - good for dev/test
}

variable "postgresql_storage_mb" {
  description = "Storage for PostgreSQL in MB (min 32768MB for Flexible Server)"
  type        = number
  default     = 32768 # 32 GB
}

variable "acr_name" {
  description = "Name of your existing Azure Container Registry (globally unique)"
  type        = string
  # Example: default = "youruniqueacrname"
  # No default - Terraform will prompt you, or you can set it here to your ACR name
  # MAKE SURE THIS MATCHES THE ACR YOU CREATED MANUALLY
}

# variable "acr_login_server" {
#   description = "Login server of your existing Azure Container Registry (e.g., youruniqueacrname.azurecr.io)"
#   type        = string
  # Example: default = "youruniqueacrname.azurecr.io"
  # No default - Terraform will prompt you, or you can set it here to your ACR login server
  # MAKE SURE THIS MATCHES THE ACR YOU CREATED MANUALLY
# }

variable "docker_image_repository" {
  description = "Name of your image repository in ACR (e.g., if image is 'myacr.io/mybillingapp:latest', this is 'mybillingapp')"
  type        = string
  default     = "mybillingapp" # CHANGE THIS to match your image name in ACR
}

variable "docker_image_tag" {
  description = "Tag of your application image in ACR (e.g., latest)"
  type        = string
  default     = "latest"
}

variable "vm_size" {
  description = "Size for the Virtual Machine"
  type        = string
  default     = "Standard_B1s" # 1 vCPU, 1 GiB RAM - good for dev/test
}

variable "vm_admin_username" {
  description = "Admin username for the Linux VM"
  type        = string
  default     = "azureuser"
}

variable "vm_admin_password" {
  description = "Admin password for the Linux VM. For production, use SSH keys."
  type        = string
  sensitive   = true
  # No default - Terraform will prompt you for this value
}

variable "my_public_ip_for_ssh" {
  description = "Your public IP address to allow SSH access to the VM (e.g., '1.2.3.4/32'). Get yours from 'curl ifconfig.me'."
  type        = string
  default     = "0.0.0.0/0" # WARNING: For demo only. Replace with "YOUR_IP/32" for better security.
}

variable "app_container_port" {
  description = "Port your application inside the container listens on (e.g., 5000 for Flask)"
  type        = number
  default     = 5000 # This should match the EXPOSE port in your Dockerfile
}

variable "app_host_port" {
  description = "Port on the VM to map to the container's app port (e.g., 80 or 5000)"
  type        = number
  default     = 5000 # Can be 80 for standard HTTP, or same as container port
}