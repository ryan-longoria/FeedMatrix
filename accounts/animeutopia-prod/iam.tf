################################################################################
## IAM
################################################################################

#############################
# IAM Policy for Lambda
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
# IAM Policy for S3
#############################

resource "aws_iam_policy" "s3_full_policy" {
  name        = "anime_s3_full_policy"
  description = "Policy to allow Lambda full access to S3"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = "s3:*",
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_s3_full_policy" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_full_policy.arn
}

#############################
# IAM Policy for Step Functions
#############################

resource "aws_iam_role" "step_functions_role" {
  name = "anime_step_functions_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "step_functions_policy" {
  name = "anime_step_functions_policy"
  role = aws_iam_role.step_functions_role.id
  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect : "Allow",
        Action : [
          "lambda:InvokeFunction"
        ],
        Resource : [
          aws_lambda_function.fetch_rss.arn,
          aws_lambda_function.process_content.arn,
          aws_lambda_function.store_data.arn,
          aws_lambda_function.render_video.arn,
          aws_lambda_function.notify_post.arn
        ]
      }
    ]
  })
}

#############################
# IAM Policy for CloudWatch/EventBridge
#############################

resource "aws_iam_role" "eventbridge_role" {
  name = "eventbridge_step_functions_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "eventbridge_policy" {
  name        = "eventbridge_step_functions_policy"
  description = "Policy for CloudWatch Event to start Step Functions executions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = "states:StartExecution",
      Resource = aws_sfn_state_machine.anime_workflow.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_eventbridge_policy" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}
