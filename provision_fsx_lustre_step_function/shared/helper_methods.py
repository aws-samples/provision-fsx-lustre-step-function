import importlib
from typing import Any

import boto3
import botocore
from botocore.exceptions import ClientError

from provision_fsx_lustre_step_function.shared.lambda_test_context import (
    LambdaTestContext,
)
from provision_fsx_lustre_step_function.shared.stack_constants import *


def module_loader(module_name: str, path: str) -> Any:
    loader = importlib.machinery.SourceFileLoader(module_name, path)
    spec = importlib.util.spec_from_loader(module_name, loader)
    function = importlib.util.module_from_spec(spec)
    loader.exec_module(function)

    handler = function.handler
    return handler


def setup_test_context(module_name: str) -> LambdaTestContext:
    return LambdaTestContext(module_name)


orig = botocore.client.BaseClient._make_api_call
aws_call_history = {}


def mock_make_api_call(self, operation_name, kwarg):
    service_id = self._service_model.service_id
    key = f"{service_id}:{operation_name}"

    if key not in aws_call_history:
        aws_call_history[key] = 0

    aws_call_history[key] = aws_call_history[key] + 1

    if service_id == SERVICE_ID_FSX:
        return fsx_stub(self, operation_name, kwarg)
    elif service_id == SERVICE_ID_CW:
        return cloudwatch_stub(self, operation_name, kwarg)

    return orig(self, operation_name, kwarg)


fsx_status_lookup = {
    TEST_FSX_ID_1: AVAILABLE,
    TEST_FSX_ID_2: CREATING,
    TEST_FSX_ID_3: FAILED,
    TEST_FSX_ID_4: DELETING,
    TEST_FSX_ID_5: MISCONFIGURED,
    TEST_FSX_ID_6: UPDATING,
    TEST_FSX_ID_7: MISCONFIGURED_UNAVAILABLE,
}


def fsx_stub(self, operation_name, kwarg):
    if operation_name == FSX_CREATE_OPERATION:
        print(kwarg)
        if kwarg[LUSTRE_CONFIG_PROPERTY][IMPORT_PATH] == VALID_TEST_URL:
            return {
                FILESYSTEM_PROPERTY: {
                    FILESYSTEM_ID_PROPERTY: "some_filesystem_id",
                    DNS_NAME_PROPERTY: "some_dns_name",
                    LIFECYCLE_PROPERTY: "CREATING",
                    LUSTRE_CONFIG_PROPERTY: {
                        MOUNT_NAME_PROPERTY: "some_mount_name",
                    },
                }
            }
        elif kwarg[LUSTRE_CONFIG_PROPERTY][IMPORT_PATH] == INVALID_TEST_URL:
            return {}
        else:
            raise ClientError(
                {"Error": {"Code": "Code", "Message": "api error"}},
                operation_name=operation_name,
            )
    elif operation_name == FSX_DESCRIBE_OPERATION:
        id = kwarg[FILESYSTEM_IDS_PROPERTY][0]
        if id in fsx_status_lookup:
            return {
                FILESYSTEMS_PROPERTY: [
                    {
                        FILESYSTEM_ID: kwarg[FILESYSTEM_IDS_PROPERTY][0],
                        LIFECYCLE_PROPERTY: fsx_status_lookup[id],
                    }
                ]
            }
        else:
            raise ClientError(
                {"Error": {"Code": "Code", "Message": "api error"}},
                operation_name=operation_name,
            )
    else:
        return orig(self, operation_name, kwarg)


def cloudwatch_stub(self, operation_name, kwarg):
    if operation_name == CW_PUT_METRIC_ALARM_OPERATION:
        print(kwarg)
        if kwarg[DIMESIONS_PROPERTY][0][VALUE_PROPERTY] == TEST_FSX_ID_1:
            return {}
        else:
            raise ClientError(
                {"Error": {"Code": "Code", "Message": "api error"}},
                operation_name=operation_name,
            )
    else:
        return orig(self, operation_name, kwarg)
