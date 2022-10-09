import pathlib

import aws_cdk.assertions as assertions
import pytest
from aws_cdk import App

from provision_fsx_lustre_step_function.provision_fsx_lustre_step_function_stack import (
    ProvisionFsxLustreStepFunctionStack,
)
from provision_fsx_lustre_step_function.shared.stack_constants import *

script_dir = pathlib.Path(__file__).parent.parent.parent
lambda_file_path = str(script_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER))
lambda_layer_file_path = str(
    script_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER, LAMBDA_LAYER_FOLDER)
)


@pytest.fixture(scope="module")
def template():
    """
    Generate a mock stack that embeds the orchestrator construct for testing
    """

    app = App()

    stack = ProvisionFsxLustreStepFunctionStack(
        app,
        "provision-fsx-lustre-step-function",
        vpc_id="some_vpc_id",
        subnet_id="some_subnet_id",
        lambda_file_path=lambda_file_path,
        lambda_layer_file_path=lambda_layer_file_path,
    )

    return assertions.Template.from_stack(stack)


def test_lambda_created(template: assertions.Template):
    """
    Validates that the Stack creation generated 2 Lambdas
    - Provision FSx Filesystem
    - Check Provision Status
    :param template: the CDK Stack template
    :return: None
    """
    template.resource_count_is("AWS::Lambda::Function", 2)


def test_bucket_created(template: assertions.Template):
    """
    Validates that the Stack creation generated 1 S3 Bucket
    - 1 S3 Bucket to link to the FSx Filesystem
    :param template: the CDK Stack template
    :return: None
    """
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_sns_topic_created(template: assertions.Template):
    """
    Validates that the Stack creation generated 1 SNS Topic
    - 1 SNS Topic to send CloudWatch Alarm Notification
    :param template: the CDK Stack template
    :return: None
    """
    template.resource_count_is("AWS::SNS::Topic", 1)


def test_has_outputs(template: assertions.Template):
    template.has_output("*", {"Export": {"Name": "SfnFsxProvisionArn"}})
    template.has_output("*", {"Export": {"Name": "SfnFsxProvisionName"}})
