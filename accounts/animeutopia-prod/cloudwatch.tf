################################################################################
## Cloudwatch
################################################################################

resource "aws_cloudwatch_event_rule" "workflow_schedule" {
  name                = "anime_workflow_schedule"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "state_machine_target" {
  rule      = aws_cloudwatch_event_rule.workflow_schedule.name
  target_id = "StepFunctionStateMachine"
  arn       = aws_sfn_state_machine.anime_workflow.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}