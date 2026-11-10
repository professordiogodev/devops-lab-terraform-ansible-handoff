# PROVIDED.
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "my_ip_cidr" {
  description = "Your public IP as a /32. ./setup.sh writes it to terraform.tfvars (not committed)."
  type        = string

  validation {
    condition     = can(cidrhost(var.my_ip_cidr, 0)) && endswith(var.my_ip_cidr, "/32")
    error_message = "my_ip_cidr must be a single address in CIDR form, for example 203.0.113.7/32."
  }
}

variable "public_key_path" {
  description = "Public half of the lab SSH key created by ./setup.sh"
  type        = string
  default     = "../keys/id_ed25519.pub"
}
