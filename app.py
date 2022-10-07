#!/usr/bin/env python3

from aws_cdk import App

from provision_fsx_lustre_step_function.provision_fsx_lustre_step_function_stack import (
    ProvisionFsxLustreStepFunctionStack,
)

app = App()
ProvisionFsxLustreStepFunctionStack(
    app,
    "provision-fsx-lustre-step-function",
    vpc_id="vpc-0ff0590a918062b01",  # TODO: replace this value with your vpc_id to be able to deploy
    subnet_id="subnet-09c5b207d2d87dc15",  # TODO: replace this value with a subnet_id from your vpc to deploy

)

app.synth()
