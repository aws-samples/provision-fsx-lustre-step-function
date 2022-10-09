import os
from typing import Any, Dict

import boto3
import jsonpickle
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

if os.environ.get("TESTING"):
    from provision_fsx_lustre_step_function.lambdas.fsx_provision.constants import *
else:
    from constants import *


tracer = Tracer()  # Sets service via POWERTOOLS_SERVICE_NAME env var
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext):
    """This lambda initiates the creation operation for an FSx for Lustre Filesystem

    Args:
        event (Dict[str, Any]): The AWS Lambda Event Source Request
        context (LambdaContext): The AWS Lambda Context for running this execution

    Raises:
        ValueError: "FSx Filesystem creation failure."
        Exception: "Error provisioning fsx filesystem."

    Returns:
        response (Dict[str, Any]): An object containing the information regarding the provisioning status
    """

    logger.info("## EVENT\r %s", jsonpickle.encode(event, unpicklable=False))
    logger.info("## CONTEXT\r %s", jsonpickle.encode(context, unpicklable=False))
    partition_size = DEFAULT_FSX_PARTITION_SIZE

    s3_bucket_import_url = os.environ[S3_BUCKET_IMPORT_URL]
    s3_bucket_export_url = os.environ[S3_BUCKET_EXPORT_URL]
    security_group_id = os.environ[FSX_SG_ID]
    subnet_id = os.environ[FSX_SUBNET_ID]

    client = get_fsx_client()

    try:
        result = client.create_file_system(
            FileSystemType=LUSTRE_FILESYSTEM_TYPE,
            StorageCapacity=partition_size,
            StorageType=STORAGE_TYPE,
            SubnetIds=[subnet_id],
            SecurityGroupIds=[security_group_id],
            LustreConfiguration={
                IMPORT_PATH: s3_bucket_import_url,
                EXPORT_PATH: s3_bucket_export_url,
                DEPLOYMENT_TYPE: LUSTRE_DEPLOYMENT_TYPE,
                DATA_COMPRESSION_TYPE: LZ4_DATA_COMPRESSION_TYPE,
            },
        )

        if not result or not result[FILESYSTEM_PROPERTY]:
            raise ValueError("FSx Filesystem creation failure.")

        response = {
            FILESYSTEM_ID: result[FILESYSTEM_PROPERTY][FILESYSTEM_ID_PROPERTY],
            FILESYSTEM_DNS_NAME: result[FILESYSTEM_PROPERTY][DNS_NAME_PROPERTY],
            FILESYSTEM_MOUNT_NAME: result[FILESYSTEM_PROPERTY][LUSTRE_CONFIG_PROPERTY][
                MOUNT_NAME_PROPERTY
            ],
            FILESYSTEM_LIFECYCLE: result[FILESYSTEM_PROPERTY][LIFECYCLE_PROPERTY],
        }
        logger.info(jsonpickle.encode(response, unpicklable=False))
    except ClientError as e:
        logger.exception("Error provisioning fsx filesystem.")
        error_response = {
            "operation_name": e.operation_name,
            "error": True,
            "details": jsonpickle.encode(e, unpicklable=False),
        }
        raise Exception(error_response)

    return response


def get_fsx_client():
    return boto3.client(BOTO3_FSX)
