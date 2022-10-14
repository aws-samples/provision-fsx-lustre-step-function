import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from provision_fsx_lustre_step_function.shared.helper_methods import (
    mock_make_api_call,
    module_loader,
    setup_test_context,
)
from provision_fsx_lustre_step_function.shared.lambda_test_context import (
    LambdaTestContext,
)
from provision_fsx_lustre_step_function.shared.stack_constants import *

logger = logging.getLogger()

MODULE_NAME = "fsx_provision"

base_dir = Path(__file__).parent.parent.parent
function_path = str(
    base_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER, MODULE_NAME, LAMBDA_FILE_NAME)
)


def test_fsx_provision_success(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch.dict(
        ENV_VARS,
        {
            S3_BUCKET_IMPORT_URL: "some_url",
            S3_BUCKET_EXPORT_URL: "some_url",
            FSX_SG_ID: "some_id",
            FSX_SUBNET_ID: "some_id",
        },
    )
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    result = handler({}, context)

    assert FILESYSTEM_ID in result


def test_fsx_provision_success(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch.dict(
        ENV_VARS,
        {
            S3_BUCKET_IMPORT_URL: VALID_TEST_URL,
            S3_BUCKET_EXPORT_URL: VALID_TEST_URL,
            FSX_SG_ID: SOME_ID,
            FSX_SUBNET_ID: SOME_ID,
        },
    )
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    result = handler({}, context)

    assert FILESYSTEM_ID in result
    assert FILESYSTEM_DNS_NAME in result
    assert FILESYSTEM_MOUNT_NAME in result
    assert result[FILESYSTEM_LIFECYCLE] == CREATING


def test_fsx_provision_creation_failure(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch.dict(
        ENV_VARS,
        {
            S3_BUCKET_IMPORT_URL: INVALID_TEST_URL,
            S3_BUCKET_EXPORT_URL: INVALID_TEST_URL,
            FSX_SG_ID: SOME_ID,
            FSX_SUBNET_ID: SOME_ID,
        },
    )
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    with pytest.raises(Exception) as exc_info:
        handler({}, context)

    assert issubclass(exc_info.type, ValueError)


def test_fsx_provision_api_failure(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch.dict(
        ENV_VARS,
        {
            S3_BUCKET_IMPORT_URL: "throws_exception",
            S3_BUCKET_EXPORT_URL: INVALID_TEST_URL,
            FSX_SG_ID: SOME_ID,
            FSX_SUBNET_ID: SOME_ID,
        },
    )
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    with pytest.raises(Exception) as exc_info:
        handler({}, context)

    assert exc_info.value.args[0].get("error")
