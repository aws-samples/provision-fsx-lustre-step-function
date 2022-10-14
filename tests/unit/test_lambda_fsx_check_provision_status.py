import logging
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
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

MODULE_NAME = "fsx_check_provision_status"

base_dir = Path(__file__).parent.parent.parent
function_path = str(
    base_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER, MODULE_NAME, LAMBDA_FILE_NAME)
)


def setup_mocker(mocker: MockerFixture):
    mocker.patch(BOTO_MAKE_API_CALL, new=mock_make_api_call)
    mocker.patch.dict(
        ENV_VARS,
        {
            FX_PROVISION_ALARM_EVALUATION_PERIODS: "123",
            FX_PROVISION_ALARM_THRESHOLD: "123",
            FX_PROVISION_ALARM_PERIOD: "123",
            FX_PROVISION_ALARM_STATISTIC: "some_statistic",
            CW_ALARM_TOPIC: "some_topic",
        },
    )


@pytest.mark.parametrize(
    "fsx_id,fsx_status",
    [
        (TEST_FSX_ID_1, AVAILABLE),
        (TEST_FSX_ID_2, CREATING),
        (TEST_FSX_ID_3, FAILED),
        (TEST_FSX_ID_4, DELETING),
        (TEST_FSX_ID_5, MISCONFIGURED),
        (TEST_FSX_ID_6, UPDATING),
        (TEST_FSX_ID_7, MISCONFIGURED_UNAVAILABLE),
    ],
)
def test_fsx_check_provision_status_success(fsx_id, fsx_status, mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    setup_mocker(mocker)

    result = handler({FILESYSTEM_ID: fsx_id}, context)

    assert FILESYSTEM_ID in result
    assert result[FILESYSTEM_LIFECYCLE] == fsx_status


def test_fsx_check_provision_status_fail_invalid_id(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    setup_mocker(mocker)

    with pytest.raises(Exception) as exc_info:
        handler({FILESYSTEM_ID: "invalid_id"}, context)

    assert exc_info.type == Exception


def test_fsx_check_provision_status_fail_no_id(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    setup_mocker(mocker)

    with pytest.raises(Exception) as exc_info:
        handler({}, context)

    assert issubclass(exc_info.type, ValueError)


def test_fsx_check_provision_status_fail_with_error(mocker: MockerFixture):

    handler = module_loader(MODULE_NAME, function_path)
    context: LambdaTestContext = setup_test_context(MODULE_NAME)
    setup_mocker(mocker)

    with pytest.raises(Exception) as exc_info:
        handler({FILESYSTEM_ID: "error_id"}, context)

    assert exc_info.value.args[0].get("error")
