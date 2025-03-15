################################################################################
## Terraform Variables
################################################################################

variable "aws_account_ids" {
  description = "The AWS Account ID. Used for configuring the provider and defining ECS resources."
  type = object({
    sharedservices = string
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
  default     = "prod"
}

variable "terraform_backend_bucket" {
  description = "The S3 bucket used to store Terraform state."
  type        = string
}

variable "app_name" {
  description = "Base name or prefix for resources (e.g., backstage)."
  type        = string
  default     = "backstage"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "List of CIDRs for public subnets."
  type        = list(string)
  default     = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "List of CIDRs for private subnets."
  type        = list(string)
  default     = ["10.0.2.0/24", "10.0.3.0/24"]
}

variable "db_name" {
  description = "Name of the PostgreSQL database for Backstage."
  type        = string
  default     = "backstage"
}

variable "db_username" {
  description = "PostgreSQL database user name."
  type        = string
  default     = "backstage_user"
}

variable "db_password" {
  description = "PostgreSQL database password (store securely in tfvars or secret)."
  type        = string
  default     = "ChangeMe123!"
}

variable "backstage_domain" {
  description = "The domain name for the Backstage ALB"
  type        = string
  default     = "backstage.feedutopia.com"
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM cert for the Backstage domain."
  type        = string
  default     = "arn:aws:acm:us-east-2:825765422855:certificate/20392fd3-e0a5-4c7d-ab03-b9fcb1afc1dd"
}

variable "cognito_domain" {
  description = "Unique prefix for the Cognito User Pool domain (e.g., backstage-auth)."
  type        = string
  default     = "backstage-auth"
}

variable "techdocs_bucket" {
  description = "S3 bucket name for TechDocs storage."
  type        = string
  default     = "backstage-techdocs-bucket"
}
