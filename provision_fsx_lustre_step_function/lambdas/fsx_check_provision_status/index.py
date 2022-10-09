import os
from typing import Any

import boto3
import jsonpickle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from check_status_request import CheckStatusRequest

if os.environ.get("TESTING"):
    from provision_fsx_lustre_step_function.lambdas.fsx_check_provision_status.constants import *
else:
    from constants import *


tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
@event_source(data_class=CheckStatusRequest)
def handler(event: CheckStatusRequest, context: LambdaContext):
    """This lambda checks the status of the creation operation for an FSx for Lustre Filesystem

    Args:
        event (CheckStatusRequest): The AWS Lambda Event Source Request
        context (LambdaContext): The AWS Lambda Context for running this execution

    Raises:
        ValueError: FSx FileSystem ID is missing
        ValueError: "FSx Filesystem with ID not found"
        Exception: "Error checking FSx provisioning status."

    Returns:
        response (Dict[str, Any]): An object containing the information regarding the provisioning status
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
            raise ValueError(f"FSx Filesystem with ID: {event.filesystem_id} not found")

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
        logger.exception("Error checking FSx provisioning status.")
        error_response = {
            "operation_name": e.operation_name,
            "error": True,
            "details": jsonpickle.encode(e, unpicklable=False),
        }
        raise Exception(error_response)

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
