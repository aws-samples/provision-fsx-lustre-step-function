#!/usr/bin/env python3

import pathlib

from aws_cdk import App, Aspects
from cdk_nag import AwsSolutionsChecks

from provision_fsx_lustre_step_function.provision_fsx_lustre_step_function_stack import (
    ProvisionFsxLustreStepFunctionStack,
)
from provision_fsx_lustre_step_function.shared.stack_constants import *

script_dir = pathlib.Path(__file__).parent
lambda_file_path = str(script_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER))
lambda_layer_file_path = str(
    script_dir.joinpath(STACK_FOLDER, LAMBDA_FOLDER, LAMBDA_LAYER_FOLDER)
)

vpc_id = REPLACE_THIS  # TODO: replace this value with your vpc_id to be able to deploy
subnet_id = (
    REPLACE_THIS  # TODO: replace this value with a subnet_id from your vpc to deploy
)

app = App()
ProvisionFsxLustreStepFunctionStack(
    app,
    "provision-fsx-lustre-step-function",
    vpc_id=vpc_id,
    subnet_id=subnet_id,
    lambda_file_path=lambda_file_path,
    lambda_layer_file_path=lambda_layer_file_path,
)

Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
