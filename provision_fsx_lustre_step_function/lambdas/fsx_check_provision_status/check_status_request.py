from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from constants import *


class CheckStatusRequest(DictWrapper):
    """Data Class to simplify the retrieval of values from the event"""

    @property
    def filesystem_id(self) -> str:
        return self[FILESYSTEM_ID]
