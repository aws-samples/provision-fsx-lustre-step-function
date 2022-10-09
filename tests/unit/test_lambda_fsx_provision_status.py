# import base64
# import io
# import json
# import zipfile
# from uuid import uuid4

# import boto3
# from botocore.exceptions import ClientError
# from moto import mock_iam, mock_lambda

# _lambda_region = "us-east-1"


# @mock_lambda
# def mock_fsx_provision_status(lambda_name):
#     conn = boto3.client("lambda", _lambda_region)
#     function_name = lambda_name
#     zip_content = get_test_zip_file()
#     conn.create_function(
#         FunctionName=function_name,
#         Runtime="python3.8",
#         Role=get_role_name(),
#         Handler="index.lambda_handler",
#         Code={"ZipFile": zip_content},
#         Description="test lambda function",
#         Timeout=30,
#         MemorySize=128,
#         Publish=True,
#     )
#     response = conn.invoke(FunctionName=function_name, InvocationType="RequestResponse")
#     lambda_resp = response["Payload"].read().decode("utf-8")
#     json_resp = json.loads(lambda_resp)
#     assert json_resp["fsxFilesystemLifecycle"] == "AVAILABLE"


# @mock_lambda
# def test_invoke_lambda():
#     provisioned_lambda = mock_fsx_provision_status("fsx_provision_status")


# def _process_lambda(func_str):
#     zip_output = io.BytesIO()
#     zip_file = zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED)
#     zip_file.writestr("index.py", func_str)
#     zip_file.close()
#     zip_output.seek(0)
#     return zip_output.read()


# def get_test_zip_file():
#     pfunc = """
# def lambda_handler(event, context):
#     return {
#         "fsxFilesystemLifecycle": "AVAILABLE",
#     }
# """
#     return _process_lambda(pfunc)


# def get_role_name():
#     with mock_iam():
#         iam = boto3.client("iam", region_name=_lambda_region)
#         try:
#             return iam.get_role(RoleName="my-role")["Role"]["Arn"]
#         except ClientError:
#             return iam.create_role(
#                 RoleName="my-role",
#                 AssumeRolePolicyDocument="some policy",
#                 Path="/my-path/",
#             )["Role"]["Arn"]
