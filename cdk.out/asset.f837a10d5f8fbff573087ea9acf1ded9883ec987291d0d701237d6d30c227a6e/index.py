import os
from typing import Any, Dict

import boto3
import jsonpickle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
logger = Logger()

# provisioning lambda property names
DEFAULT_FSX_PARTITION_SIZE = 1200
PARTITION_SIZE = "partitionSize"
S3_BUCKET_IMPORT_URL = "S3_BUCKET_IMPORT_URL"
S3_BUCKET_EXPORT_URL = "S3_BUCKET_EXPORT_URL"
FSX_SG_ID = "FSX_SG_ID"
FSX_SUBNET_ID = "FSX_SUBNET_ID"

# payload property names
FILESYSTEM_ID = "fsxFilesystemId"
FILESYSTEM_DNS_NAME = "fsxFilesystemDnsName"
FILESYSTEM_MOUNT_NAME = "fsxFilesystemMountName"
FILESYSTEM_LIFECYCLE = "fsxFilesystemLifecycle"
ITEMS = "items"
PAYLOAD = "Payload"

# fsx api response property names
FILESYSTEM_PROPERTY = "FileSystem"
FILESYSTEM_ID_PROPERTY = "FileSystemId"
DNS_NAME_PROPERTY = "DNSName"
LUSTRE_CONFIG_PROPERTY = "LustreConfiguration"
MOUNT_NAME_PROPERTY = "MountName"
LIFECYCLE_PROPERTY = "Lifecycle"
FILESYSTEMS_PROPERTY = "FileSystems"


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext):
    """This lambda initiates the creation operation for an FSx for Lustre Filesystem

    Keyword arguments:
        event - The AWS Lambda Event Source Request
        context - The AWS Lambda Context for running this execution
    """
    logger.info("## EVENT\r" + jsonpickle.encode(event, unpicklable=False))
    logger.info("## CONTEXT\r" + jsonpickle.encode(context, unpicklable=False))
    partition_size = DEFAULT_FSX_PARTITION_SIZE
    if PARTITION_SIZE in event:
        partition_size = event[PARTITION_SIZE]

    s3_bucket_import_url = os.environ[S3_BUCKET_IMPORT_URL]
    s3_bucket_export_url = os.environ[S3_BUCKET_EXPORT_URL]
    security_group_id = os.environ[FSX_SG_ID]
    subnet_id = os.environ[FSX_SUBNET_ID]

    client = get_fsx_client()

    try:
        response = client.create_file_system(
            FileSystemType="LUSTRE",
            StorageCapacity=partition_size,
            StorageType="SSD",
            SubnetIds=[subnet_id],
            SecurityGroupIds=[security_group_id],
            LustreConfiguration={
                "ImportPath": s3_bucket_import_url,
                "ExportPath": s3_bucket_export_url,
                "DeploymentType": "SCRATCH_2",
                "DataCompressionType": "LZ4",
            },
        )

        if not response or not response[FILESYSTEM_PROPERTY]:
            raise ValueError("FSx Filesystem creation failure.")

        event[FILESYSTEM_ID] = response[FILESYSTEM_PROPERTY][FILESYSTEM_ID_PROPERTY]
        event[FILESYSTEM_DNS_NAME] = response[FILESYSTEM_PROPERTY][DNS_NAME_PROPERTY]
        event[FILESYSTEM_MOUNT_NAME] = response[FILESYSTEM_PROPERTY][
            LUSTRE_CONFIG_PROPERTY
        ][MOUNT_NAME_PROPERTY]
        event[FILESYSTEM_LIFECYCLE] = response[FILESYSTEM_PROPERTY][LIFECYCLE_PROPERTY]

        logger.info(jsonpickle.encode(event))
    except ClientError as e:
        event = {"error": True, "details": jsonpickle.encode(e)}
        raise Exception(event)

    return event


def get_fsx_client():
    return boto3.client("fsx")
