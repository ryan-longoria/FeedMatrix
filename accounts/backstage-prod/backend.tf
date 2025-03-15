################################################################################
## Backend Declaration - Configured by `--backend-config=backends/...`
################################################################################

terraform {
  backend "s3" {
    bucket   = "prod-backstage-backend-bucket"
    key      = "tfstate/backstage/terraform.tfstate"
    region   = "us-east-2"
    role_arn = "arn:aws:iam::825765422855:role/TerraformExecutionRole"
  }
}