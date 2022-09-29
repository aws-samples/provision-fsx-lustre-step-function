import os
from typing import Any

import boto3
import jsonpickle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from check_status_request import CheckStatusRequest
from constants import *

tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
@event_source(data_class=CheckStatusRequest)
def handler(event: CheckStatusRequest, context: LambdaContext):
    """This lambda checks the status of the creation operation for an FSx for Lustre Filesystem

    Keyword arguments:
        event - The AWS Lambda Event Source Request
        context - The AWS Lambda Context for running this execution
    """
    logger.info("## EVENT\r %s", jsonpickle.encode(event, unpicklable=False))
    logger.info("## CONTEXT\r %s", jsonpickle.encode(context, unpicklable=False))

    if not event.filesystem_id:
        raise ValueError("FSx FileSystem ID is missing")

    client = get_fsx_client()

    try:
        response = client.describe_file_systems(FileSystemIds=[event.filesystem_id])
        if (
            not response[FILESYSTEMS_PROPERTY]
            or len(response[FILESYSTEMS_PROPERTY]) < 1
        ):
            raise ValueError(
                "FSx Filesystem with ID: {} not found".format(event.filesystem_id)
            )

        filesystem = response[FILESYSTEMS_PROPERTY][0]

        filesystem_lifecycle = filesystem[LIFECYCLE_PROPERTY]

        response = {
            FILESYSTEM_ID: event.filesystem_id,
            FILESYSTEM_LIFECYCLE: filesystem_lifecycle,
        }

        if filesystem_lifecycle == AVAILABLE:
            logger.debug("Creating CloudWatch Alarm")
            add_metric_alarm(event.filesystem_id)

        logger.info(jsonpickle.encode(event))
    except ClientError as e:
        logger.exception("Error checking provisioning status.")
        event = {"error": True, "details": jsonpickle.encode(e, unpicklable=False)}
        raise Exception(event)

    return response


def get_fsx_client() -> Any:
    return boto3.client(BOTO3_FSX)


def get_cloudwatch_client() -> Any:
    return boto3.client(BOTO3_CLOUDWATCH)


def add_metric_alarm(filesystem_id: str) -> Any:
    cloudwatch_client = get_cloudwatch_client()
    cw_response = cloudwatch_client.put_metric_alarm(
        AlarmName=f"FsxAlarm-{filesystem_id}",
        MetricName=METRIC_NAME,
        Namespace=METRIC_NAMESPACE,
        EvaluationPeriods=int(os.environ[FX_PROVISION_ALARM_EVALUATION_PERIODS]),
        Threshold=int(os.environ[FX_PROVISION_ALARM_THRESHOLD]),
        ComparisonOperator=METRIC_COMPARISON_OPERATOR,
        Period=int(os.environ[FX_PROVISION_ALARM_PERIOD]),
        Statistic=os.environ[FX_PROVISION_ALARM_STATISTIC],
        Dimensions=[{NAME: "filesystem_id", VALUE: filesystem_id}],
        AlarmActions=[os.environ[CW_ALARM_TOPIC]],
    )
    return cw_response
