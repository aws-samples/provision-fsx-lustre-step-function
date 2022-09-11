import os
from typing import Any, Dict

import boto3
import jsonpickle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
logger = Logger()

FILESYSTEM_ID = "fsxFilesystemId"
FILESYSTEM_LIFECYCLE = "fsxFilesystemLifecycle"
PAYLOAD = "Payload"
PARAMETERS = "Parameters"
OUTPUT = "Output"

# fsx api response property names
FILESYSTEMS_PROPERTY = "FileSystems"
LIFECYCLE_PROPERTY = "Lifecycle"
AVAILABLE = "AVAILABLE"

# fsx alarm properties
FX_PROVISION_ALARM_EVALUATION_PERIODS = "FX_PROVISION_ALARM_EVALUATION_PERIODS"
FX_PROVISION_ALARM_THRESHOLD = "FX_PROVISION_ALARM_THRESHOLD"
FX_PROVISION_ALARM_PERIOD = "FX_PROVISION_ALARM_PERIOD"
FX_PROVISION_ALARM_STATISTIC = "FX_PROVISION_ALARM_STATISTIC"
CW_ALARM_TOPIC = "CW_ALARM_TOPIC"


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext):
    """This lambda checks the status of the creation operation for an FSx for Lustre Filesystem

    Keyword arguments:
        event - The AWS Lambda Event Source Request
        context - The AWS Lambda Context for running this execution
    """
    logger.info("## EVENT\r" + jsonpickle.encode(event, unpicklable=False))
    logger.info("## CONTEXT\r" + jsonpickle.encode(context, unpicklable=False))

    if FILESYSTEM_ID not in event:
        raise ValueError("FSx FileSystem ID is missing")

    filesystem_id = event[FILESYSTEM_ID]

    client = get_fsx_client()

    try:
        response = client.describe_file_systems(FileSystemIds=[filesystem_id])
        if (
            not response[FILESYSTEMS_PROPERTY]
            or len(response[FILESYSTEMS_PROPERTY]) < 1
        ):
            raise ValueError(
                "FSx Filesystem with ID: {} not found".format(filesystem_id)
            )

        filesystem = response[FILESYSTEMS_PROPERTY][0]

        filesystem_lifecycle = filesystem[LIFECYCLE_PROPERTY]

        event[FILESYSTEM_ID] = filesystem_id
        event[FILESYSTEM_LIFECYCLE] = filesystem_lifecycle

        if filesystem_lifecycle == AVAILABLE:
            logger.debug("Creating CloudWatch Alarm")
            add_metric_alarm(filesystem_id)

        logger.info(jsonpickle.encode(event))
    except ClientError as e:
        event = {"error": True, "details": jsonpickle.encode(e)}
        raise Exception(event)

    return event


def get_fsx_client():
    return boto3.client("fsx")


def get_cloudwatch_client():
    return boto3.client("cloudwatch")


def add_metric_alarm(filesystem_id: str):
    cloudwatch_client = get_cloudwatch_client()
    cw_response = cloudwatch_client.put_metric_alarm(
        AlarmName="FsxAlarm-{}".format(filesystem_id),
        MetricName="FreeDataStorageCapacity",
        Namespace="AWS/FSx",
        EvaluationPeriods=int(os.environ[FX_PROVISION_ALARM_EVALUATION_PERIODS]),
        Threshold=int(os.environ[FX_PROVISION_ALARM_THRESHOLD]),
        ComparisonOperator="LessThanOrEqualToThreshold",
        Period=int(os.environ[FX_PROVISION_ALARM_PERIOD]),
        Statistic=os.environ[FX_PROVISION_ALARM_STATISTIC],
        Dimensions=[{"Name": "filesystem_id", "Value": filesystem_id}],
        AlarmActions=[os.environ[CW_ALARM_TOPIC]],
    )
    return cw_response
