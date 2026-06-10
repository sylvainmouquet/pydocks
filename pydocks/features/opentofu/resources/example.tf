# Simple example configuration file
terraform {
  required_version = ">= 1.0.0"
}

variable "test_variable" {
  type    = string
  default = "test_value"
}

output "test_output" {
  value = var.test_variable
}

# Example local resource
resource "local_file" "example" {
  content  = "This is an example file created by OpenTofu"
  filename = "${path.module}/example.txt"
}