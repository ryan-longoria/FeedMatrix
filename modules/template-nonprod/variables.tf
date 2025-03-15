################################################################################
## Terraform Variables
################################################################################

variable "aws_account_ids" {
  description = "The AWS Account ID. Used for configuring the provider and defining ECS resources."
  type = object({
    project = string
  })
}

variable "aws_region" {
  description = "The AWS region to deploy resources."
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "The environment name (nonprod, prod)."
  type        = string
  default     = "nonprod"
}