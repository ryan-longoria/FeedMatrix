resource "aws_cognito_user_pool" "backstage" {
  name                     = "backstage-user-pool"
  auto_verified_attributes = ["email"]
  alias_attributes         = ["email"]
  mfa_configuration        = "OFF"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  tags = { Name = "backstage-user-pool" }
}

resource "aws_cognito_user_pool_domain" "backstage" {
  domain       = "backstage-auth-feedutopia"
  user_pool_id = aws_cognito_user_pool.backstage.id
}

resource "aws_cognito_user_pool_client" "backstage" {
  name            = "backstage-alb-client"
  user_pool_id    = aws_cognito_user_pool.backstage.id
  generate_secret = true

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = ["https://backstage.feedutopia.com/oauth2/idpresponse"]
  logout_urls   = ["https://backstage.feedutopia.com/"]
}
