################################################################################
## Lambda
################################################################################

#############################
# IAM Role for Lambda Functions
#############################
resource "aws_iam_role" "lambda_role" {
  name = "anime_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#############################
# IAM Policy for Lambda Functions
#############################
resource "aws_iam_policy" "ec2_control_policy" {
  name        = "anime_ec2_control_policy"
  description = "Policy to allow Lambda functions to start and stop EC2 instances"
  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Action : [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ],
        Resource : "arn:aws:ec2:${var.aws_region}:${data.aws_caller_identity.current.account_id}:instance/${var.ec2_instance_id}"
      }
    ]
  })
}

resource "aws_iam_policy" "ssm_send_command_policy" {
  name        = "anime_ssm_full_policy"
  description = "Policy to allow Lambda functions full access to SSM"
  policy      = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Action: "ssm:*",
        Resource: "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_ssm_send_command_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.ssm_send_command_policy.arn
}

resource "aws_iam_role_policy_attachment" "attach_ec2_control_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.ec2_control_policy.arn
}

resource "aws_iam_policy" "ec2_describe_policy" {
  name        = "anime_ec2_describe_policy"
  description = "Policy to allow Lambda functions to describe EC2 instances"
  policy      = jsonencode({
    Version   : "2012-10-17",
    Statement : [
      {
        Effect   : "Allow",
        Action   : "ec2:DescribeInstances",
        Resource : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_ec2_describe_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.ec2_describe_policy.arn
}

resource "aws_iam_policy" "s3_list_and_get_policy" {
  name        = "anime_s3_full_policy"
  description = "Policy to allow Lambda full access to S3 for the prod-animeutopia-media-bucket"
  policy      = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Action: "s3:*",
        Resource: [
          "arn:aws:s3:::prod-animeutopia-media-bucket",
          "arn:aws:s3:::prod-animeutopia-media-bucket/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_list_and_get_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_list_and_get_policy.arn
}

resource "aws_iam_policy" "sns_publish_policy" {
  name        = "anime_sns_publish_policy"
  description = "Policy to allow Lambda functions to publish to SNS topics for notifications"
  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Action : [
          "sns:Publish"
        ],
        Resource : aws_sns_topic.anime_notifications.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_sns_publish_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.sns_publish_policy.arn
}

data "aws_caller_identity" "current" {}

#############################
# Lambda Functions
#############################
resource "aws_lambda_function" "fetch_rss" {
  function_name      = "fetch_rss"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/fetch_rss/fetch_rss.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/fetch_rss/fetch_rss.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10
}

resource "aws_lambda_function" "process_content" {
  function_name      = "process_content"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/process_content/process_content.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/process_content/process_content.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      IMAGE_MAGICK_EXE = "/opt/bin/magick"
    }
  }

  layers = [
    "arn:aws:lambda:us-east-2:481665084477:layer:imagick-layer:1"
  ]
}

resource "aws_lambda_function" "store_data" {
  function_name      = "store_data"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/store_data/store_data.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/store_data/store_data.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.media_bucket.bucket
    }
  }
}

resource "aws_lambda_function" "render_video" {
  function_name      = "render_video"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/render_video/render_video.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/render_video/render_video.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 20

  environment {
    variables = {
      INSTANCE_ID = var.ec2_instance_id
    }
  }
}

resource "aws_lambda_function" "save_video" {
  function_name      = "save_video"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/save_video/save_video.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/save_video/save_video.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 20

  environment {
    variables = {
      INSTANCE_ID   = var.ec2_instance_id,
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "start_instance" {
  function_name      = "start_instance"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/start_instance/start_instance.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/start_instance/start_instance.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      EC2_INSTANCE_ID = var.ec2_instance_id
    }
  }
}

resource "aws_lambda_function" "stop_instance" {
  function_name      = "stop_instance"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/stop_instance/stop_instance.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/stop_instance/stop_instance.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      EC2_INSTANCE_ID = var.ec2_instance_id
    }
  }
}

resource "aws_lambda_function" "notify_post" {
  function_name      = "notify_post"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/notify_post/notify_post.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/notify_post/notify_post.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.anime_notifications.arn,
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}
