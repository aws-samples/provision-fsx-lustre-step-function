BOTO_MAKE_API_CALL = "botocore.client.BaseClient._make_api_call"
SERVICE_ID_FSX = "FSx"
SERVICE_ID_CW = "CloudWatch"
FSX_CREATE_OPERATION = "CreateFileSystem"
CW_PUT_METRIC_ALARM_OPERATION = "PutMetricAlarm"
FSX_DESCRIBE_OPERATION = "DescribeFileSystems"
ENV_VARS = "os.environ"

FILESYSTEM_ID = "fsxFilesystemId"
FILESYSTEM_DNS_NAME = "fsxFilesystemDnsName"
FILESYSTEM_MOUNT_NAME = "fsxFilesystemMountName"
FILESYSTEM_LIFECYCLE = "fsxFilesystemLifecycle"

# fsx api response property names
FILESYSTEM_PROPERTY = "FileSystem"
FILESYSTEM_IDS_PROPERTY = "FileSystemIds"
FILESYSTEM_ID_PROPERTY = "FileSystemId"
DNS_NAME_PROPERTY = "DNSName"
LUSTRE_CONFIG_PROPERTY = "LustreConfiguration"
MOUNT_NAME_PROPERTY = "MountName"
LIFECYCLE_PROPERTY = "Lifecycle"
FILESYSTEMS_PROPERTY = "FileSystems"
IMPORT_PATH = "ImportPath"
EXPORT_PATH = "ExportPath"
DEPLOYMENT_TYPE = "DeploymentType"
DATA_COMPRESSION_TYPE = "DataCompressionType"

# fsx provisioning parameters
DEFAULT_FSX_PARTITION_SIZE = 1200
FSX_INBOUND_PORT = 988
FSX_INBOUND_PORT_RANGE_START = 1021
FSX_INBOUND_PORT_RANGE_END = 1023
FSX_SG_ID = "FSX_SG_ID"
FSX_SUBNET_ID = "FSX_SUBNET_ID"
FX_PROVISION_ALARM_EVALUATION_PERIODS = "FX_PROVISION_ALARM_EVALUATION_PERIODS"
FX_PROVISION_ALARM_THRESHOLD = "FX_PROVISION_ALARM_THRESHOLD"
FX_PROVISION_ALARM_PERIOD = "FX_PROVISION_ALARM_PERIOD"
FX_PROVISION_ALARM_STATISTIC = "FX_PROVISION_ALARM_STATISTIC"

S3_BUCKET_IMPORT_URL = "S3_BUCKET_IMPORT_URL"
S3_BUCKET_EXPORT_URL = "S3_BUCKET_EXPORT_URL"
S3_URI_TEMPLATE = "s3://{}/{}"

CW_ALARM_TOPIC = "CW_ALARM_TOPIC"

# lambda parameters
FILESYSTEM_ID_PARAMETER = "fsxFilesystemId"
FILESYSTEM_LIFECYCLE_PARAMETER = "fsxFilesystemLifecycle"
FILESYSTEM_SYNC_LIFECYCLE_PARAMETER = "fsxSyncToS3Lifecycle"
FILESYSTEM_DNS_NAME_PARAMETER = "fsxFilesystemDnsName"
FILESYSTEM_MOUNT_NAME_PARAMETER = "fsxFilesystemMountName"
BUCKET_NAME_PARAMETER = "bucketName"
BUCKET_ARN_PARAMETER = "bucketArn"

# step function parameter constants
INPUT_PATH = "input_path"
PARAMETERS = "parameters"
RESULT_SELECTOR = "result_selector"
RESULT_PATH = "result_path"
OUTPUT_PATH = "output_path"

# fsx creation and sync statuses
AVAILABLE = "AVAILABLE"
CREATING = "CREATING"
FAILED = "FAILED"
DELETING = "DELETING"
MISCONFIGURED = "MISCONFIGURED"
UPDATING = "UPDATING"
MISCONFIGURED_UNAVAILABLE = "MISCONFIGURED_UNAVAILABLE"

SUCCEEDED = "SUCCEEDED"
EXECUTING = "EXECUTING"
PENDING = "PENDING"

# cloudwatch parameters
DIMESIONS_PROPERTY = "Dimensions"
VALUE_PROPERTY = "Value"

# managed policies
LAMBDA_EXECUTION_POLICY = "service-role/AWSLambdaBasicExecutionRole"
XRAY_WRITE_POLICY = "AWSXRayDaemonWriteAccess"
FSX_ACCESS_POLICY = "AmazonFSxFullAccess"

# AWS service principals
LAMBDA_SERVICE_PRINCIPAL = "lambda.amazonaws.com"
FSX_SERVICE_PRINCIPAL = "fsx.amazonaws.com"
S3_FSX_SERVICE_PRINCIPAL = "s3.data-source.lustre.fsx.amazonaws.com"

# config settings
STACK_FOLDER = "provision_fsx_lustre_step_function"
LAMBDA_LAYER_FILE_PATH = "lambda_layer_file_path"
LAMBDA_FILE_PATH = "lambda_file_path"
LAMBDA_FOLDER = "lambdas"
LAMBDA_LAYER_FOLDER = "lambda_layer"
LAMBDA_FILE_NAME = "index.py"

VENDED_LOGS_PREFIX = "/aws/vendedlogs/{}"
STATES_PREFIX = "states/"

POWERTOOLS_SERVICE_NAME = "POWERTOOLS_SERVICE_NAME"
LOG_LEVEL = "LOG_LEVEL"
LAMBDA_POWERTOOLS_LAYER = (
    "arn:aws:lambda:{}:017000801446:layer:AWSLambdaPowertoolsPython:37"
)

VPC_ID = "vpc_id"
SUBNET_ID = "subnet_id"

VALID_TEST_URL = "valid_url"
INVALID_TEST_URL = "invalid_url"
SOME_ID = "some_id"
API_ERROR = "api error"


TEST_FSX_ID_1 = "id1"
TEST_FSX_ID_2 = "id2"
TEST_FSX_ID_3 = "id3"
TEST_FSX_ID_4 = "id4"
TEST_FSX_ID_5 = "id5"
TEST_FSX_ID_6 = "id6"
TEST_FSX_ID_7 = "id7"

REPLACE_THIS = "<SOME_INVALID_ID>"

ALARM_EMAIL_ADDRESS = (
    "noreply@mailinator.com"  # TODO: Change Fake Email for Alarm Email Testing
)
