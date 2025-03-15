################################################################################
## S3
################################################################################


resource "aws_s3_bucket" "media_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "media_bucket_versioning" {
  bucket = aws_s3_bucket.media_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
