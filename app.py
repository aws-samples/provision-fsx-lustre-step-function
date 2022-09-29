#!/usr/bin/env python3

from aws_cdk import App

from provision_fsx_lustre_step_function.provision_fsx_lustre_step_function_stack import (
    ProvisionFsxLustreStepFunctionStack,
)

app = App()
ProvisionFsxLustreStepFunctionStack(
    app,
    "provision-fsx-lustre-step-function",
    vpc_id="<SOME VPC ID>",  # TODO: replace this value with your vpc_id to be able to deploy
    subnet_id="<SOME VPC SUBNET ID>",  # TODO: replace this value with a subnet_id from your vpc to deploy
)

app.synth()
