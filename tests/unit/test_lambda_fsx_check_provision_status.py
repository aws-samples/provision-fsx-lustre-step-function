import logging
from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from provision_fsx_lustre_step_function.lambdas.fsx_check_provision_status.check_status_request import CheckStatusRequest

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

MODULE_NAME = "fsx_check_provision_status"

base_dir = Path(__file__).parent.parent.parent
function_path = str(
    base_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER, MODULE_NAME, LAMBDA_FILE_NAME)
)


def test_fsx_check_provision_status_success(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    result = handler({FILESYSTEM_ID: "valid_id"}, context)

    assert FILESYSTEM_ID in result

def test_fsx_check_provision_status_success_creating(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    result = handler({FILESYSTEM_ID: "valid_id"}, context)

    assert FILESYSTEM_ID in result
    assert result[FILESYSTEM_LIFECYCLE] == CREATING

def test_fsx_check_provision_status_success_available(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch.dict(
        ENV_VARS,
        {
            FX_PROVISION_ALARM_EVALUATION_PERIODS: "123",
            FX_PROVISION_ALARM_THRESHOLD: "123",
            FX_PROVISION_ALARM_PERIOD: "123",
            FX_PROVISION_ALARM_STATISTIC: "some_statistic",
            CW_ALARM_TOPIC: "some_topic"
        },
    )
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    result = handler({FILESYSTEM_ID: "valid_id_av"}, context)

    assert FILESYSTEM_ID in result
    assert result[FILESYSTEM_LIFECYCLE] == AVAILABLE

def test_fsx_check_provision_status_fail_invalid_id(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    with pytest.raises(Exception) as exc_info:
        handler({FILESYSTEM_ID: "invalid_id"}, context)

    assert issubclass(exc_info.type, (KeyError))

def test_fsx_check_provision_status_fail_no_id(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    with pytest.raises(Exception) as exc_info:
        handler({}, context)

    assert issubclass(exc_info.type, (KeyError))


def test_fsx_check_provision_status_fail_with_error(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)

    with pytest.raises(Exception) as exc_info:
        handler({FILESYSTEM_ID: "error_id"}, context)

    assert exc_info.value.args[0].get("error")
