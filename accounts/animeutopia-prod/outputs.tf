################################################################################
## Outputs
################################################################################

output "s3_bucket_name" {
  description = "The S3 bucket name used for storing media assets."
  value       = aws_s3_bucket.media_bucket.bucket
}

output "state_machine_arn" {
  description = "The ARN of the Step Functions state machine."
  value       = aws_sfn_state_machine.anime_workflow.arn
}
