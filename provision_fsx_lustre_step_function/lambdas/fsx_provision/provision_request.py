import os

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

if os.environ.get("TESTING"):
    from provision_fsx_lustre_step_function.lambdas.fsx_provision.constants import *
else:
    from constants import *


class ProvisionRequest(DictWrapper):
    """Data Class to simplify the retrieval of values from the event"""

    @property
    def partition_size(self) -> str:
        return (
            self[PARTITION_SIZE]
            if PARTITION_SIZE in self
            else DEFAULT_FSX_PARTITION_SIZE
        )
