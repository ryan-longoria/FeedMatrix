################################################################################
## Providers Declared Here - Configured by variables
################################################################################

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      DeployedBy = "Terraform"
    }
  }

  assume_role {
    role_arn = "arn:aws:iam::${var.aws_account_id}:role/TerraformExecutionRole"
  }
}
