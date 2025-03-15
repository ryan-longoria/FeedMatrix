aws_region               = "us-east-2"
terraform_backend_bucket = "prod-backstage-backend-bucket"
environment              = "prod"

app_name = "backstage"
vpc_cidr = "10.10.0.0/16"

public_subnet_cidrs  = ["10.10.0.0/24", "10.10.1.0/24"]
private_subnet_cidrs = ["10.10.2.0/24", "10.10.3.0/24"]

db_name     = "backstage"
db_username = "bs_user"
db_password = "ReallySecurePassword123!"

backstage_domain    = "backstage.feedutopia.com"
acm_certificate_arn = ""
cognito_domain      = "backstage-auth-feedutopia"
techdocs_bucket     = "backstage-techdocs-feedutopia"
