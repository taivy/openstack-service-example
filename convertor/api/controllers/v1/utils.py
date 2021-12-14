import jsonpatch
from oslo_config import cfg
from oslo_utils import reflection
from oslo_utils import uuidutils
import pecan
import wsme

from convertor._i18n import _
from convertor.common import utils
from convertor import objects

CONF = cfg.CONF


JSONPATCH_EXCEPTIONS = (jsonpatch.JsonPatchException,
                        jsonpatch.JsonPointerException,
                        KeyError)


def validate_limit(limit):
    if limit is None:
        return CONF.api.max_limit

    if limit <= 0:
        # Case where we don't a valid limit value
        raise wsme.exc.ClientSideError(_("Limit must be positive"))

    if limit and not CONF.api.max_limit:
        # Case where we don't have an upper limit
        return limit

    return min(CONF.api.max_limit, limit)


def validate_sort_dir(sort_dir):
    if sort_dir not in ['asc', 'desc']:
        raise wsme.exc.ClientSideError(_("Invalid sort direction: %s. "
                                         "Acceptable values are "
                                         "'asc' or 'desc'") % sort_dir)


def validate_sort_key(sort_key, allowed_fields):
    # Very lightweight validation for now
    if sort_key not in allowed_fields:
        raise wsme.exc.ClientSideError(
            _("Invalid sort key: %s") % sort_key)


def validate_search_filters(filters, allowed_fields):
    # Very lightweight validation for now
    # todo: improve this (e.g. https://www.parse.com/docs/rest/guide/#queries)
    for filter_name in filters:
        if filter_name not in allowed_fields:
            raise wsme.exc.ClientSideError(
                _("Invalid filter: %s") % filter_name)


def get_resource(resource, resource_id, eager=False):
    """Get the resource from the uuid, id or logical name.
    :param resource: the resource type.
    :param resource_id: the UUID, ID or logical name of the resource.
    :returns: The resource.
    """
    resource = getattr(objects, resource)

    _get = None
    if utils.is_int_like(resource_id):
        resource_id = int(resource_id)
        _get = resource.get
    elif uuidutils.is_uuid_like(resource_id):
        _get = resource.get_by_uuid
    else:
        _get = resource.get_by_name

    method_signature = reflection.get_signature(_get)
    if 'eager' in method_signature.parameters:
        return _get(pecan.request.context, resource_id, eager=eager)

    return _get(pecan.request.context, resource_id)
