resource "aws_security_group" "alb" {
  name        = "backstage-alb-sg"
  description = "Allow inbound HTTP/HTTPS to ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description      = "Allow HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }

  ingress {
    description      = "Allow HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }

  tags = {
    Name = "backstage-alb-sg"
  }
}

resource "aws_security_group" "ecs" {
  name        = "backstage-ecs-sg"
  description = "Allow ALB to access ECS tasks on Backstage port"
  vpc_id      = aws_vpc.main.id

  ingress {
    description      = "Allow Backstage port from ALB"
    from_port        = 7007
    to_port          = 7007
    protocol         = "tcp"
    security_groups  = [aws_security_group.alb.id]
    cidr_blocks      = []
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    self             = false
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }

  tags = { Name = "backstage-ecs-sg" }
}

resource "aws_lb" "frontend" {
  name               = "backstage-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public1.id, aws_subnet.public2.id]
  tags               = { Name = "backstage-alb" }
}

resource "aws_lb_target_group" "backstage" {
  name        = "backstage-tg"
  port        = 7007
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 5
    matcher             = "200"
  }
  tags = { Name = "backstage-tg" }
}

resource "aws_lb_listener" "frontend_https" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate_validation.cert_validation_complete.certificate_arn
  ssl_policy        = "ELBSecurityPolicy-2016-08"

  default_action {
    type  = "authenticate-cognito"
    order = 1
    authenticate_cognito {
      user_pool_arn              = aws_cognito_user_pool.backstage.arn
      user_pool_client_id        = aws_cognito_user_pool_client.backstage.id
      user_pool_domain           = aws_cognito_user_pool_domain.backstage.domain
      on_unauthenticated_request = "authenticate"
    }
  }

  default_action {
    type             = "forward"
    order            = 2
    target_group_arn = aws_lb_target_group.backstage.arn
  }
}

resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
