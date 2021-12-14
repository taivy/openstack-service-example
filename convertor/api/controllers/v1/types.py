from oslo_serialization import jsonutils
from oslo_utils import strutils
import wsme
from wsme import types as wtypes

from convertor._i18n import _
from convertor.common import exception
from convertor.common import utils


class UuidType(wtypes.UserType):
    """A simple UUID type."""

    basetype = wtypes.text
    name = 'uuid'

    @staticmethod
    def validate(value):
        if not utils.is_uuid_like(value):
            raise exception.InvalidUUID(uuid=value)
        return value

    @staticmethod
    def frombasetype(value):
        if value is None:
            return None
        return UuidType.validate(value)


class BooleanType(wtypes.UserType):
    """A simple boolean type."""

    basetype = wtypes.text
    name = 'boolean'

    @staticmethod
    def validate(value):
        try:
            return strutils.bool_from_string(value, strict=True)
        except ValueError as e:
            # raise Invalid to return 400 (BadRequest) in the API
            raise exception.Invalid(e)

    @staticmethod
    def frombasetype(value):
        if value is None:
            return None
        return BooleanType.validate(value)


class JsonType(wtypes.UserType):
    """A simple JSON type."""

    basetype = wtypes.text
    name = 'json'

    def __str__(self):
        # These are the json serializable native types
        return ' | '.join(map(str, (wtypes.text, int, float,
                                    BooleanType, list, dict, None)))

    @staticmethod
    def validate(value):
        try:
            jsonutils.dumps(value, default=None)
        except TypeError:
            raise exception.Invalid(_('%s is not JSON serializable') % value)
        else:
            return value

    @staticmethod
    def frombasetype(value):
        return JsonType.validate(value)


uuid = UuidType()
boolean = BooleanType()
jsontype = JsonType()


class JsonPatchType(wtypes.Base):
    """A complex type that represents a single json-patch operation."""

    path = wtypes.wsattr(wtypes.StringType(pattern=r'^(/[\w-]+)+$'),
                         mandatory=True)
    op = wtypes.wsattr(wtypes.Enum(str, 'add', 'replace', 'remove'),
                       mandatory=True)
    value = wsme.wsattr(jsontype, default=wtypes.Unset)

    @staticmethod
    def internal_attrs():
        """Returns a list of internal attributes.
        Internal attributes can't be added, replaced or removed. This
        method may be overwritten by derived class.
        """
        return ['/created_at', '/id', '/links', '/updated_at',
                '/deleted_at', '/uuid']

    @staticmethod
    def mandatory_attrs():
        """Returns a list of mandatory attributes.
        Mandatory attributes can't be removed from the document. This
        method should be overwritten by derived class.
        """
        return []

    @staticmethod
    def validate(patch):
        _path = '/{0}'.format(patch.path.split('/')[1])
        if _path in patch.internal_attrs():
            msg = _("'%s' is an internal attribute and can not be updated")
            raise wsme.exc.ClientSideError(msg % patch.path)

        if patch.path in patch.mandatory_attrs() and patch.op == 'remove':
            msg = _("'%s' is a mandatory attribute and can not be removed")
            raise wsme.exc.ClientSideError(msg % patch.path)

        if patch.op != 'remove':
            if patch.value is wsme.Unset:
                msg = _("'add' and 'replace' operations needs value")
                raise wsme.exc.ClientSideError(msg)

        ret = {'path': patch.path, 'op': patch.op}
        if patch.value is not wsme.Unset:
            ret['value'] = patch.value
        return ret

