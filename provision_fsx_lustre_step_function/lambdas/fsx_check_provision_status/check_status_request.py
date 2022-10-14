import os

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if os.environ.get("TESTING"):
    from provision_fsx_lustre_step_function.lambdas.fsx_check_provision_status.constants import *
else:
    from constants import *


class CheckStatusRequest(DictWrapper):
    """Data Class to simplify the retrieval of values from the event"""

    @property
    def filesystem_id(self) -> str:
        return self[FILESYSTEM_ID]
