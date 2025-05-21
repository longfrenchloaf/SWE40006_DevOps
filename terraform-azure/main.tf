terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0" # Use a recent stable version
    }
  }
  required_version = ">= 1.0"
}

provider "azurerm" {
  features {}
  # Ensure you are logged in via `az login` and the correct subscription is set.
}

# --- Reference Existing Resources ---
# data "azurerm_resource_group" "main" {
#   name = var.resource_group_name
# }

# --- Resource Group ---
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location # This will now be "Canada Central"
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# data "azurerm_container_registry" "main" {
#   name                = var.acr_name
#   resource_group_name = azurerm_resource_group.main.name
# }

resource "azurerm_container_registry" "main" {
  name                = var.acr_name # Ensure this name is globally unique
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- Networking ---
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_prefix}-vnet"
  address_space       = var.vnet_address_space
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

resource "azurerm_subnet" "app_subnet" {
  name                 = "${var.project_prefix}-app-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.app_subnet_prefix]
}

resource "azurerm_subnet" "db_subnet" {
  name                 = "${var.project_prefix}-db-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.db_subnet_prefix]
  delegation {
    name = "fsDelegation" # Name for the delegation
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}
# --- Private DNS Zone for PostgreSQL --- # 
resource "azurerm_private_dns_zone" "postgresql" {
  # The name of the private DNS zone must match the FQDN suffix for the PostgreSQL server.
  # For flexible server, the typical pattern is `.private.postgres.database.azure.com`
  # However, to make it dynamic and tied to the server name, it's better to use the server's FQDN suffix.
  # A simpler approach for the zone name is to use a fixed suffix Azure expects.
  # The most common and reliable is "privatelink.postgres.database.azure.com" if you were using Private Link,
  # but for VNet injected flexible server, Azure often manages the A record in a zone you provide.
  # Let's use a name that clearly indicates its purpose and aligns with general practice.
  # The server will register itself in this zone.
  # The critical part is that the server needs *a* private DNS zone ID.
  # A common convention is to use the server name as part of the DNS zone, like:
  # name                = "${var.project_prefix}-pgflex.private.postgres.database.azure.com"
  # OR, more simply and usually sufficient:
  name                = "mypgflex.private.postgres.database.azure.com" # Or make it more unique: "${var.project_prefix}.postgres.private"
                                                                      # Azure will create a CNAME in the public DNS zone pointing to an A record in this private zone.
                                                                      # The key is the PostgreSQL service needs *a* private DNS zone.
                                                                      # Let's use a fixed, commonly accepted suffix.
                                                                      # After creation, check the PostgreSQL server's networking tab in Azure portal to see how it registered.
  resource_group_name = azurerm_resource_group.main.name
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- Link Private DNS Zone to VNet ---
resource "azurerm_private_dns_zone_virtual_network_link" "postgresql_vnet_link" {
  name                  = "${var.project_prefix}-pg-dns-vnet-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgresql.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = false # Flexible Server manages its own DNS record registration in the zone.
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- Azure Database for PostgreSQL Flexible Server ---
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.project_prefix}-pgflex"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15" # Or your preferred supported version
  delegated_subnet_id    = azurerm_subnet.db_subnet.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgresql.id
  administrator_login    = var.postgresql_admin_login
  administrator_password = var.postgresql_admin_password
  sku_name               = var.postgresql_sku_name
  storage_mb             = var.postgresql_storage_mb
  zone                   = "1" # Or another zone based on region availability

  public_network_access_enabled = false

  backup_retention_days = 7
  geo_redundant_backup_enabled = false

  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- VM Network Security Group ---
resource "azurerm_network_security_group" "vm_nsg" {
  name                = "${var.project_prefix}-vm-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "AllowSSH"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = var.my_public_ip_for_ssh # IMPORTANT: Restrict this!
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowAppPort"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = var.app_host_port # Port exposed on the VM
    source_address_prefix      = "*"                 # Allow from anywhere for the app
    destination_address_prefix = "*"
  }
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- VM Public IP ---
resource "azurerm_public_ip" "vm_pip" {
  name                = "${var.project_prefix}-vm-pip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static" # Static IP is generally preferred for servers
  sku                 = "Standard"
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- VM Network Interface (NIC) ---
resource "azurerm_network_interface" "vm_nic" {
  name                = "${var.project_prefix}-vm-nic"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.app_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.vm_pip.id
  }
  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# --- Associate NSG with VM's NIC ---
resource "azurerm_network_interface_security_group_association" "vm_nic_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.vm_nic.id
  network_security_group_id = azurerm_network_security_group.vm_nsg.id
}

# --- VM Custom Data (cloud-init for initial setup) ---
# This script installs Docker, logs into ACR (if admin enabled), pulls your image, and runs it.
# For ACR login: This assumes admin user is enabled on ACR.
# A more secure production approach uses Managed Identity for the VM to pull from ACR.
data "template_file" "vm_custom_data" {
  template = <<-EOF
    #cloud-config
    package_update: true
    package_upgrade: true
    packages:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg
      - lsb-release
      - docker.io

    runcmd:
      # Install Azure CLI (needed for `az acr login` if you want to use Managed Identity later)
      # - curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

      # Start and enable Docker
      - systemctl start docker
      - systemctl enable docker
      - usermod -aG docker $${vm_admin_username} # Add admin user to docker group

      # Login to ACR (This part is tricky without Managed Identity or exposing creds)
      # Option 1: Manually SSH and login if this fails (simplest for now if not using MSI)
      # Option 2: If ACR admin user is enabled (as per your `az acr create` command)
      #   You would need to securely get and use ACR admin username/password here, which is NOT recommended directly in custom_data.
      #   For this example, we'll assume you might need to SSH in and run `docker login` if the pull fails.
      #   A better way for Day 4 might be to ensure your ACR allows anonymous pull IF it's just for this temp dev.

      # Pull the Docker image
      - docker pull $${acr_login_server}/$${docker_image_repository}:$${docker_image_tag}

      # Run the Docker container
      # Ensure your application inside the container listens on 0.0.0.0:$${app_container_port}
      - docker run -d -p $${app_host_port}:$${app_container_port} \
        -e DB_HOST=$${db_server_fqdn} \
        -e DB_PORT=5432 \
        -e DB_NAME=$${db_default_database_name} \
        -e DB_USER=$${db_admin_login} \
        -e DB_PASSWORD='$${db_admin_password}' \
        --restart always \
        $${acr_login_server}/$${docker_image_repository}:$${docker_image_tag}
  EOF

  vars = {

    vm_admin_username         = var.vm_admin_username
    acr_login_server          = azurerm_container_registry.main.login_server # Comes from azurerm_container_registry.main.login_server if TF creates ACR
                                                    # For existing ACR, it's var.acr_login_server
    docker_image_repository   = var.docker_image_repository
    docker_image_tag          = var.docker_image_tag
    app_host_port             = var.app_host_port
    app_container_port        = var.app_container_port
    db_server_fqdn            = azurerm_postgresql_flexible_server.main.fqdn
    db_default_database_name  = "postgres" # Default DB for PostgreSQL, or azurerm_postgresql_flexible_server.main.name if you want a specific initial DB created with that name
    db_admin_login            = var.postgresql_admin_login
    db_admin_password         = var.postgresql_admin_password # Sensitive, be cautious
  }
}

# --- Linux Virtual Machine ---
resource "azurerm_linux_virtual_machine" "main" {
  name                            = "${var.project_prefix}-vm"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  size                            = var.vm_size
  admin_username                  = var.vm_admin_username
  admin_password                  = var.vm_admin_password
  disable_password_authentication = false # Set to true if using SSH keys exclusively

  network_interface_ids = [
    azurerm_network_interface.vm_nic.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS" # Or Standard_LRS
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy" # Ubuntu Server 22.04 LTS
    sku       = "22_04-lts-gen2"               # Or "22_04-lts" for Gen1 VM sizes
    version   = "latest"
  }

  custom_data = base64encode(data.template_file.vm_custom_data.rendered)

  # For SSH Key authentication (recommended over password for production):
  # admin_ssh_key {
  #   username   = var.vm_admin_username
  #   public_key = file("~/.ssh/id_rsa.pub") # Path to your public SSH key
  # }

  # To enable Managed Identity for secure ACR pull (recommended):
  # identity {
  #   type = "SystemAssigned"
  # }

  tags = {
    environment = "development"
    project     = var.project_prefix
  }
}

# Optional: If using Managed Identity on VM, assign "AcrPull" role to it for your ACR
# resource "azurerm_role_assignment" "vm_acr_pull" {
#   count                = azurerm_linux_virtual_machine.main.identity != null ? 1 : 0 # Only if identity is enabled
#   scope                = azurerm_container_registry.main.id
#   role_definition_name = "AcrPull"
#   principal_id         = azurerm_linux_virtual_machine.main.identity[0].principal_id
# }