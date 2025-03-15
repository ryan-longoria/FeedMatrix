resource "aws_security_group" "rds" {
  name        = "backstage-rds-sg"
  description = "Allow ECS tasks to access RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  ingress {
    description      = "Postgres from ECS tasks"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.ecs.id]
    cidr_blocks      = []
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    self             = false
  }

  egress {
    description      = "Allow all outbound traffic"
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
    Name = "backstage-rds-sg"
  }
}


resource "aws_db_subnet_group" "backstage" {
  name       = "backstage-db-subnet-group"
  subnet_ids = [aws_subnet.private1.id, aws_subnet.private2.id]
  tags       = { Name = "backstage-db-subnet-group" }
}

resource "aws_db_instance" "backstage" {
  engine              = "postgres"
  engine_version      = "14"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  storage_encrypted   = true
  multi_az            = false
  publicly_accessible = false

  db_name  = "backstage"
  username = "backstage_user"
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.backstage.name
  parameter_group_name   = "default.postgres14"

  skip_final_snapshot = true
  tags                = { Name = "backstage-db" }
}
