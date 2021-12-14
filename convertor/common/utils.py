from oslo_log import log
from oslo_utils import strutils

LOG = log.getLogger(__name__)


def safe_rstrip(value, chars=None):
    """Removes trailing characters from a string if that does not make it empty
    :param value: A string value that will be stripped.
    :param chars: Characters to remove.
    :return: Stripped value.
    """
    if not isinstance(value, str):
        LOG.warning(
            "Failed to remove trailing character. Returning original object."
            "Supplied object is not a string: %s,", value)
        return value

    return value.rstrip(chars) or value


is_int_like = strutils.is_int_like
