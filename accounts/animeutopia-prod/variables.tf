################################################################################
## Terraform Variables
################################################################################

variable "aws_account_ids" {
  description = "The AWS Account ID. Used for configuring the provider and defining ECS resources."
  type        = object({
    animeutopia = string
  })
}

variable "aws_region" {
  description = "The AWS region to deploy resources."
  type        = string
  default     = "us-east-2"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket to store media assets."
  type        = string
  default     = "animeutopia-media-bucket"
}

variable "environment" {
  description = "The environment name (nonprod, prod)."
  type        = string
  default     = "nonprod"
}

variable "terraform_backend_bucket" {
  description = "The S3 bucket used to store Terraform state."
  type        = string
  default     = "animeutopia-backend-bucket"
}

variable "teams_webhook_url" {
  description = "The Teams webhook URL used to notify when a new post is ready."
  type        = string
}