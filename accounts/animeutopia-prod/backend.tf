################################################################################
## Backend Declaration - Configured by `--backend-config=backends/...`
################################################################################

terraform {
  backend "s3" {
    bucket   = "prod-animeutopia-backend-bucket"
    key      = "tfstate/animeutopia/terraform.tfstate"
    region   = "us-east-2"
    role_arn = "arn:aws:iam::${var.aws_account_ids.animeutopia}:role/TerraformExecutionRole"
  }
}