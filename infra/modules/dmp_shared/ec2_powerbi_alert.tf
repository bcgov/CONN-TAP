# ---------------------------------------------------------------------------
# Alert when PowerBI EC2 instance has been running for more than 8 hours.
# Sends an email via SNS (optional, when powerbi_alert_email is set).
# ---------------------------------------------------------------------------

resource "aws_sns_topic" "powerbi_long_running" {
  name = "${var.powerbi_instance_name}-long-running-alert"
}

resource "aws_sns_topic_subscription" "powerbi_long_running_email" {
  count = var.powerbi_alert_email != null ? 1 : 0

  topic_arn = aws_sns_topic.powerbi_long_running.arn
  protocol  = "email"
  endpoint  = var.powerbi_alert_email
}

# Lambda: runs every hour, checks PowerBI instance uptime, publishes to SNS if > 8 hours
data "archive_file" "powerbi_uptime_checker" {
  type        = "zip"
  output_path = "${path.module}/powerbi_uptime_checker.zip"

  source {
    content  = <<-EOT
import os
import boto3
from datetime import datetime, timezone

def lambda_handler(event, context):
    instance_name = os.environ["POWERBI_INSTANCE_NAME"]
    topic_arn = os.environ["SNS_TOPIC_ARN"]
    ec2 = boto3.client("ec2")
    sns = boto3.client("sns")

    r = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [instance_name]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    for res in r.get("Reservations", []):
        for inst in res.get("Instances", []):
            launch = inst["LaunchTime"]
            if launch.tzinfo is None:
                launch = launch.replace(tzinfo=timezone.utc)
            hours = (datetime.now(timezone.utc) - launch).total_seconds() / 3600
            if hours >= 8:
                sns.publish(
                    TopicArn=topic_arn,
                    Subject="PowerBI EC2 instance running > 8 hours",
                    Message=(
                        f"Instance '{instance_name}' has been running for {hours:.1f} hours. "
                        "Consider stopping it in the EC2 console to reduce cost."
                    ),
                )
    return {}
EOT
    filename = "lambda_function.py"
  }
}

resource "aws_iam_role" "powerbi_uptime_checker" {
  name = "dmp-powerbi-uptime-checker"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "powerbi_uptime_checker" {
  name = "dmp-powerbi-uptime-checker"
  role = aws_iam_role.powerbi_uptime_checker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ec2:DescribeInstances"
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = aws_sns_topic.powerbi_long_running.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "powerbi_uptime_checker_logs" {
  role       = aws_iam_role.powerbi_uptime_checker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "powerbi_uptime_checker" {
  function_name = "${var.powerbi_instance_name}-uptime-checker"
  role          = aws_iam_role.powerbi_uptime_checker.arn
  runtime       = "python3.13"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.powerbi_uptime_checker.output_path
  source_code_hash = data.archive_file.powerbi_uptime_checker.output_base64sha256

  environment {
    variables = {
      POWERBI_INSTANCE_NAME = var.powerbi_instance_name
      SNS_TOPIC_ARN         = aws_sns_topic.powerbi_long_running.arn
    }
  }
}

resource "aws_cloudwatch_event_rule" "powerbi_uptime_checker_schedule" {
  name                = "${var.powerbi_instance_name}-uptime-check-hourly"
  description         = "Run PowerBI EC2 uptime checker every hour"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "powerbi_uptime_checker" {
  rule      = aws_cloudwatch_event_rule.powerbi_uptime_checker_schedule.name
  target_id = "PowerbiUptimeChecker"
  arn       = aws_lambda_function.powerbi_uptime_checker.arn
}

resource "aws_lambda_permission" "powerbi_uptime_checker_events" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.powerbi_uptime_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.powerbi_uptime_checker_schedule.arn
}
