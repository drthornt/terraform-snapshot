variable "customer" {}

variable "environment" {}

variable "region" {}

variable "timeout" {
  default = 3
}

variable "snap_schedule_expression" {
  default = "cron(12 23 * * ? *)"
}

variable "prune_schedule_expression" {
  default = "cron(12 2 * * ? *)"
}

resource "aws_iam_role" "lambda_snapshot_role" {
  name               = "${var.customer}-${var.region}-lambda_snapshot_role-${var.environment}"
  path               = "/"
  assume_role_policy = "${file("${path.module}/templates/snapshot-role.json")}"
}

resource "aws_iam_policy" "snapshot_policy" {
  name        = "${var.customer}-${var.region}-snapshot_policy-${var.environment}"
  path        = "/"
  description = "snapshot_policy"
  policy      = "${file("${path.module}/templates/snapshot-policy.json")}"
}

resource "aws_iam_role_policy_attachment" "snapshot_role_policy_att" {
  role       = "${aws_iam_role.lambda_snapshot_role.name}"
  policy_arn = "${aws_iam_policy.snapshot_policy.arn}"
}

output "lambda_snapshot_role_id" {
  value = "${aws_iam_role.lambda_snapshot_role.id}"
}

# taken from https://serverlesscode.com/examples/2015-10-schedule-ebs-snapshot-backups.py
# http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
resource "aws_lambda_function" "ebs_snapshot_by_tag" {
  filename         = "${path.module}/lambda_functions/ebs_snapshot_by_tag.zip"
  function_name    = "ebs_snapshot_by_tag"
  description      = "Loop through all instances with appropriate tags and create snapshots of all disks."
  role             = "${aws_iam_role.lambda_snapshot_role.arn}"
  handler          = "ebs_snapshot_by_tag.lambda_handler"
  runtime          = "python2.7"
  source_code_hash = "${base64sha256(file("${path.module}/lambda_functions/ebs_snapshot_by_tag.zip"))}"
  timeout          = "${var.timeout}"
  publish          = "false"
}

resource "aws_lambda_function" "ebs_snapshot_prune_by_tag" {
  filename         = "${path.module}/lambda_functions/ebs_snapshot_prune_by_tag.zip"
  function_name    = "ebs_snapshot_prune_by_tag"
  description      = "removed snapshots with a deleton date tag older than today"
  role             = "${aws_iam_role.lambda_snapshot_role.arn}"
  handler          = "ebs_snapshot_prune_by_tag.lambda_handler"
  runtime          = "python2.7"
  source_code_hash = "${base64sha256(file("${path.module}/lambda_functions/ebs_snapshot_prune_by_tag.zip"))}"
  timeout          = "${var.timeout}"
  publish          = "false"
}

resource "aws_cloudwatch_event_rule" "daily_ebs_snapshot_rule" {
  name = "daily_ebs_snapshot_rule"

  # schedule_expression = "cron(12 23 * * ? *)"
  schedule_expression = "${var.snap_schedule_expression}"
}

resource "aws_cloudwatch_event_rule" "daily_ebs_snapshot_prune_rule" {
  name = "daily_ebs_snapshot_prune_rule"

  #schedule_expression = "cron(12 2 * * ? *)"
  schedule_expression = "${var.prune_schedule_expression}"
}

resource "aws_cloudwatch_event_target" "snap" {
  target_id = "snap"
  rule      = "${aws_cloudwatch_event_rule.daily_ebs_snapshot_rule.name}"
  arn       = "${aws_lambda_function.ebs_snapshot_by_tag.arn}"
}

resource "aws_cloudwatch_event_target" "prune" {
  target_id = "prune"
  rule      = "${aws_cloudwatch_event_rule.daily_ebs_snapshot_prune_rule.name}"
  arn       = "${aws_lambda_function.ebs_snapshot_prune_by_tag.arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_snap" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.ebs_snapshot_by_tag.function_name}"
  principal     = "events.amazonaws.com"

  # source_account = "111122223333"

  # source_arn     = "arn:aws:events:eu-west-1:111122223333:rule/RunDaily"

  # qualifier      = "${aws_lambda_alias.test_alias.name}"
}

resource "aws_lambda_permission" "allow_cloudwatch_prune" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.ebs_snapshot_prune_by_tag.function_name}"
  principal     = "events.amazonaws.com"

  # source_account = "111122223333"

  # source_arn     = "arn:aws:events:eu-west-1:111122223333:rule/RunDaily"

  # qualifier      = "${aws_lambda_alias.test_alias.name}"
}
