#!/usr/bin/env python3

from aws_cdk import App

from provision_fsx_lustre_step_function.provision_fsx_lustre_step_function_stack import (
    ProvisionFsxLustreStepFunctionStack,
)

app = App()
ProvisionFsxLustreStepFunctionStack(
    app,
    "provision-fsx-lustre-step-function",
    vpc_id="vpc-0c224fab5e167df49"
    # vpc_id = "<SOME VPC ID>"  # TODO: replace this value what a vpc_id to be able to deploy
)

app.synth()
