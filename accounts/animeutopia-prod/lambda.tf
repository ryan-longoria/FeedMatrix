################################################################################
## Lambda
################################################################################

#############################
# fetch_rss
#############################

resource "aws_lambda_function" "fetch_rss" {
  function_name    = "fetch_rss"
  filename         = "${path.module}/artifacts/scripts/fetch_rss/fetch_rss.zip"
  source_code_hash = filebase64sha256("${path.module}/artifacts/scripts/fetch_rss/fetch_rss.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_role.arn
  timeout          = 10
}

#############################
# process_content
#############################

resource "aws_lambda_function" "process_content" {
  function_name    = "process_content"
  filename         = "${path.module}/artifacts/scripts/process_content/process_content.zip"
  source_code_hash = filebase64sha256("${path.module}/artifacts/scripts/process_content/process_content.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_role.arn
  timeout          = 10
  environment {
    variables = {
      IMAGE_MAGICK_EXE = "/bin/magick"
    }
  }
  layers = [
    "arn:aws:lambda:${var.aws_region}:481665084477:layer:imagick-layer:1"
  ]
}

#############################
# store_data
#############################

resource "aws_lambda_function" "store_data" {
  function_name    = "store_data"
  filename         = "${path.module}/artifacts/scripts/store_data/store_data.zip"
  source_code_hash = filebase64sha256("${path.module}/artifacts/scripts/store_data/store_data.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_role.arn
  timeout          = 10
  environment {
    variables = {
      BUCKET_NAME = var.s3_bucket_name
    }
  }
}

#############################
# render_video
#############################

resource "aws_lambda_function" "render_video" {
  function_name = "render_video"
  package_type  = "Image"
  image_uri     = "481665084477.dkr.ecr.us-east-2.amazonaws.com/render_video_repository@sha256:62d0bd0bc8a36c68201ec227e08739523cf6fff83bf57f15954f9e49120fb658"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 300
  memory_size   = 3008
  environment {
    variables = {
      TARGET_BUCKET = var.s3_bucket_name
      FFMPEG_PATH   = "/opt/bin/ffmpeg"
    }
  }
}

#############################
# notify_post
#############################

resource "aws_lambda_function" "notify_post" {
  function_name    = "notify_post"
  filename         = "${path.module}/artifacts/scripts/notify_post/notify_post.zip"
  source_code_hash = filebase64sha256("${path.module}/artifacts/scripts/notify_post/notify_post.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  role             = aws_iam_role.lambda_role.arn
  timeout          = 10
  environment {
    variables = {
      TEAMS_WEBHOOK_URL = var.teams_webhook_url,
      TARGET_BUCKET     = var.s3_bucket_name
    }
  }
}
