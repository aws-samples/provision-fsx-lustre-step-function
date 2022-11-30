from aws_cdk import CfnOutput, Duration, Fn, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_lambda_python_alpha as py_lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from cdk_nag import NagSuppressions
from constructs import Construct

from provision_fsx_lustre_step_function.shared.stack_constants import *


class ProvisionFsxLustreStepFunctionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        lambda_file_path = kwargs[LAMBDA_FILE_PATH]
        lambda_layer_file_path = kwargs[LAMBDA_LAYER_FILE_PATH]

        vpc_id = kwargs[VPC_ID]
        subnet_id = kwargs[SUBNET_ID]

        if vpc_id == REPLACE_THIS:
            raise KeyError("VPC ID is not set.")

        if subnet_id == REPLACE_THIS:
            raise KeyError("Subnet ID is not set.")

        powertools_layer_version = _lambda.LayerVersion.from_layer_version_arn(
            self,
            id="LambdaPowerTools",
            layer_version_arn=LAMBDA_POWERTOOLS_LAYER.format(self.region),
        )

        # - IaC to setup Fail step
        fail_state = sfn.Fail(self, "FailState")

        # - IaC to set up Succeed step
        succeed_state = sfn.Succeed(self, "SucceedState")

        # IaC to set up 2 minute wait (120 seconds) for FSx Status Check
        fsx_wait_state = sfn.Wait(
            self,
            "ProvisioningWaitState",
            time=sfn.WaitTime.duration(Duration.seconds(120)),
        )

        availability_zones = Fn.get_azs()
        vpc = ec2.Vpc.from_vpc_attributes(
            self,
            "VPC",
            vpc_id=vpc_id,
            availability_zones=availability_zones,
        )

        fsx_security_group = ec2.SecurityGroup(
            self, "FSxSecurityGroup", vpc=vpc, allow_all_outbound=True
        )

        fsx_security_group.connections.allow_from(
            fsx_security_group, ec2.Port.tcp(FSX_INBOUND_PORT)
        )

        fsx_security_group.connections.allow_from(
            fsx_security_group,
            ec2.Port.tcp_range(
                FSX_INBOUND_PORT_RANGE_START, FSX_INBOUND_PORT_RANGE_END
            ),
        )

        # - IaC to provision S3 Bucket for data
        s3_bucket = self.provision_s3_bucket()

        fsx_mgmt_role = self.build_fsx_create_role(s3_bucket.bucket_arn)

        bucket_import_path = ""
        bucket_export_path = ""
        s3_bucket_import_url = S3_URI_TEMPLATE.format(
            s3_bucket.bucket_name, bucket_import_path
        )
        s3_bucket_export_url = S3_URI_TEMPLATE.format(
            s3_bucket.bucket_name, bucket_export_path
        )

        # - IAC to provision topic to send CloudWatch Alarm notifications
        cw_alarm_topic = sns.Topic(
            self,
            id="cloudwatch_alarms",
        )
        cw_alarm_topic.add_subscription(
            sns_subscriptions.EmailSubscription(email_address=ALARM_EMAIL_ADDRESS)
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/{cw_alarm_topic.node.id}/Resource",
            [
                {
                    "id": "AwsSolutions-SNS2",
                    "reason": "Encryption is not necessary for a sample to demonstate setting up a CloudWatch Alarm Topic",
                },
                {
                    "id": "AwsSolutions-SNS3",
                    "reason": "Enabling SSL is not an option via CDK",
                },
            ],
        )

        # IaC for Lambda Layer that will be used to share dependencies
        lambda_dependency_layer = py_lambda.PythonLayerVersion(
            self,
            "LambdaDependencyLayer",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            removal_policy=RemovalPolicy.DESTROY,
            entry=lambda_layer_file_path,
        )

        # - IaC to deploy Lambda provision FSx for Lustre Filesystem
        fsx_provision_lambda = py_lambda.PythonFunction(
            self,
            id="FsxProvisionHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name="fsx-provision-handler",
            description="Lambda to initiate provisioning of FSx for Lustre filesystem",
            role=fsx_mgmt_role,
            environment={
                S3_BUCKET_IMPORT_URL: s3_bucket_import_url,
                S3_BUCKET_EXPORT_URL: s3_bucket_export_url,
                FSX_SG_ID: fsx_security_group.security_group_id,
                FSX_SUBNET_ID: subnet_id,
                "POWERTOOLS_SERVICE_NAME": "fsx_provision",
                "LOG_LEVEL": "INFO",
            },
            layers=[lambda_dependency_layer],
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=128,
            timeout=Duration.seconds(900),
            entry="{}/{}".format(lambda_file_path, "fsx_provision"),
            insights_version=_lambda.LambdaInsightsVersion.VERSION_1_0_135_0,
            profiling=True,
        )

        fsx_provision_lambda.add_layers(powertools_layer_version)

        # - IaC for Task to provision FSx for Lustre Filesystem
        provision_task = sfn_tasks.LambdaInvoke(
            self,
            "InvokeFsxProvisionTask",
            lambda_function=fsx_provision_lambda,
            output_path="$.Payload",
        )

        # - IaC to deploy Lambda to check provision status of FSx for Lustre Filesystem
        fsx_check_provision_lambda = py_lambda.PythonFunction(
            self,
            id="CheckFsxProvisionHandler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            function_name="fsx-check-provision-handler",
            description="Lambda to check the provisioning status of FSx for Lustre filesystem",
            role=fsx_mgmt_role,
            environment={
                FX_PROVISION_ALARM_EVALUATION_PERIODS: "5",
                FX_PROVISION_ALARM_THRESHOLD: "1099511627776",
                FX_PROVISION_ALARM_PERIOD: "60",
                FX_PROVISION_ALARM_STATISTIC: "Minimum",
                CW_ALARM_TOPIC: cw_alarm_topic.topic_arn,
                POWERTOOLS_SERVICE_NAME: "fsx_provision",
                LOG_LEVEL: "INFO",
            },
            layers=[lambda_dependency_layer],
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=128,
            timeout=Duration.seconds(900),
            entry="{}/{}".format(lambda_file_path, "fsx_check_provision_status"),
            insights_version=_lambda.LambdaInsightsVersion.VERSION_1_0_135_0,
            profiling=True,
        )

        fsx_check_provision_lambda.add_layers(powertools_layer_version)

        # - IaC for Task to check provision status of FSx for Lustre Filesystem
        check_provision_task = sfn_tasks.LambdaInvoke(
            self,
            "InvokeCheckFsxProvisionTask",
            lambda_function=fsx_check_provision_lambda,
            output_path="$.Payload",
        )

        check_provision_status_choice = sfn.Choice(self, "FSxProvisioningStatusCheck")
        check_provision_status_choice.when(
            sfn.Condition.string_equals(
                "$.{}".format(FILESYSTEM_LIFECYCLE_PARAMETER), AVAILABLE
            ),
            succeed_state,
        )
        check_provision_status_choice.when(
            sfn.Condition.string_equals(
                "$.{}".format(FILESYSTEM_LIFECYCLE_PARAMETER), CREATING
            ),
            fsx_wait_state,
        )
        check_provision_status_choice.otherwise(fail_state)

        fsx_wait_state.next(check_provision_task)

        check_provision_task.next(check_provision_status_choice)

        provision_task.next(check_provision_task)

        log_group_name = "{}{}".format(STATES_PREFIX, "fsx-provisioning-logs")

        log_group = logs.LogGroup(
            self,
            id="FsxProvisioningLogs",
            log_group_name=VENDED_LOGS_PREFIX.format(log_group_name),
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.SIX_MONTHS,
        )

        log_options = sfn.LogOptions(destination=log_group, level=sfn.LogLevel.ALL)

        _state_machine = sfn.StateMachine(
            self,
            id="ProvisionFsxWorkflow",
            state_machine_type=sfn.StateMachineType.STANDARD,
            definition=provision_task,
            logs=log_options,
            tracing_enabled=True,
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/{_state_machine.node.id}/Role/DefaultPolicy/Resource",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "This role is for Lambdas that are dynamically provisioning FSx Filesystems. It needs to be more permissive.",
                }
            ],
        )

        # Outputs
        CfnOutput(
            self,
            "sfn_fsx_provision_arn",
            value=_state_machine.state_machine_arn,
            export_name="SfnFsxProvisionArn",
            description="FSx Provisioning Step Function ARN",
        )
        CfnOutput(
            self,
            "sfn_fsx_provision_name",
            value=_state_machine.state_machine_name,
            export_name="SfnFsxProvisionName",
            description="FSx Provisioning Step Function Name",
        )

    def build_fsx_create_role(self, resource_arn: str):
        network_iam_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        network_iam_policy.add_all_resources()
        network_iam_policy.add_actions(
            "ec2:DescribeSecurityGroups", "ec2:DescribeVpcs", "ec2:DescribeSubnets"
        )

        s3_bucket_iam_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        s3_bucket_iam_policy.add_resources(resource_arn)
        s3_bucket_iam_policy.add_actions(
            "s3:GetBucketPublicAccessBlock",
            "s3:GetBucketPolicyStatus",
            "s3:GetEncryptionConfiguration",
            "s3:PutBucketPublicAccessBlock",
            "s3:ListBucketVersions",
            "s3:PutBucketAcl",
            "s3:PutBucketPolicy",
            "s3:PutBucketNotification",
            "s3:ListBucket",
            "s3:GetBucketVersioning",
            "s3:GetBucketPolicy",
        )

        cloudwatch_iam_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        cloudwatch_iam_policy.add_resources("arn:aws:cloudwatch:*:*:alarm:FsxAlarm-*")
        cloudwatch_iam_policy.add_actions(
            "cloudwatch:PutMetricAlarm", "cloudwatch:DeleteAlarms"
        )

        service_linked_role_policy_s3 = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        service_linked_role_policy_s3.add_resources(
            f"arn:aws:iam::*:role/aws-service-role/{S3_FSX_SERVICE_PRINCIPAL}/*"
        )
        service_linked_role_policy_s3.add_actions(
            "iam:CreateServiceLinkedRole", "iam:AttachRolePolicy", "iam:PutRolePolicy"
        )
        service_linked_role_policy_s3.add_condition(
            "StringLike", {"iam:AWSServiceName": S3_FSX_SERVICE_PRINCIPAL}
        )

        service_linked_role_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        service_linked_role_policy.add_resources(
            f"arn:aws:iam::*:role/aws-service-role/{FSX_SERVICE_PRINCIPAL}/*"
        )
        service_linked_role_policy.add_actions(
            "iam:CreateServiceLinkedRole", "iam:AttachRolePolicy", "iam:PutRolePolicy"
        )
        service_linked_role_policy.add_condition(
            "StringLike", {"iam:AWSServiceName": FSX_SERVICE_PRINCIPAL}
        )

        fsx_iam_policy = iam.PolicyStatement(effect=iam.Effect.ALLOW)
        fsx_iam_policy.add_all_resources()
        fsx_iam_policy.add_actions(
            "fsx:DescribeFileSystems",
            "fsx:CreateFileSystem",
            "fsx:UntagResource",
            "fsx:TagResource",
        )

        manage_fsx_role = iam.Role(
            self,
            "ManageFsxRole",
            assumed_by=iam.ServicePrincipal(LAMBDA_SERVICE_PRINCIPAL),
        )

        manage_fsx_role.add_to_policy(network_iam_policy)
        manage_fsx_role.add_to_policy(s3_bucket_iam_policy)
        manage_fsx_role.add_to_policy(service_linked_role_policy)
        manage_fsx_role.add_to_policy(service_linked_role_policy_s3)
        manage_fsx_role.add_to_policy(cloudwatch_iam_policy)
        manage_fsx_role.add_to_policy(fsx_iam_policy)
        manage_fsx_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(LAMBDA_EXECUTION_POLICY)
        )
        manage_fsx_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(XRAY_WRITE_POLICY)
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/{manage_fsx_role.node.id}/Resource",
            [
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "Sample should be able to use Managed Policies. Actual implementation should create custom policy.",
                }
            ],
        )

        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/{manage_fsx_role.node.id}/DefaultPolicy/Resource",
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "This role is for Lambdas that are dynamically provisioning FSx Filesystems. It needs to be more permissive.",
                }
            ],
        )

        return manage_fsx_role

    def provision_s3_bucket(self):
        access_logs_bucket = s3.Bucket(
            self,
            "AccessLogsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )
        NagSuppressions.add_resource_suppressions_by_path(
            self,
            f"/{self.stack_name}/{access_logs_bucket.node.id}/Resource",
            [
                {
                    "id": "AwsSolutions-S1",
                    "reason": "Access Log Bucket doesn't need Access Log Bucket",
                }
            ],
        )

        s3_bucket = s3.Bucket(
            self,
            id="DataSyncBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.days(180),
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30),
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        ),
                    ],
                )
            ],
            server_access_logs_bucket=access_logs_bucket,
            server_access_logs_prefix="logs",
        )
        return s3_bucket
