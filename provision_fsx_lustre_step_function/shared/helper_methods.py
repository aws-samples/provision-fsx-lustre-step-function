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

    return orig(self, operation_name, kwarg)


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
    else:
        return orig(self, operation_name, kwarg)
