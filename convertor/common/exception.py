import functools
import sys

from http import HTTPStatus
from keystoneclient import exceptions as keystone_exceptions
from oslo_config import cfg
from oslo_log import log

from convertor._i18n import _

LOG = log.getLogger(__name__)

CONF = cfg.CONF


def wrap_keystone_exception(func):
    """Wrap keystone exceptions and throw Watcher specific exceptions."""
    @functools.wraps(func)
    def wrapped(*args, **kw):
        try:
            return func(*args, **kw)
        except keystone_exceptions.AuthorizationFailure:
            raise AuthorizationFailure(
                client=func.__name__, reason=sys.exc_info()[1])
        except keystone_exceptions.ClientException:
            raise AuthorizationFailure(
                client=func.__name__,
                reason=(_('Unexpected keystone client error occurred: %s')
                        % sys.exc_info()[1]))
    return wrapped


class ConvertorException(Exception):
    """Base Convertor Exception
    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.
    """
    msg_fmt = _("An unknown exception occurred")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                # kwargs doesn't match a variable in msg_fmt
                # log the issue and the kwargs
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.items():
                    LOG.error("%(name)s: %(value)s",
                              {'name': name, 'value': value})

                if CONF.fatal_exception_format_errors:
                    raise
                else:
                    # at least get the core msg_fmt out if something happened
                    message = self.msg_fmt

        super(ConvertorException, self).__init__(message)

    def __str__(self):
        """Encode to utf-8 then wsme api can consume it as well"""
        return self.args[0]

    def __unicode__(self):
        return str(self.args[0])

    def format_message(self):
        if self.__class__.__name__.endswith('_Remote'):
            return self.args[0]
        else:
            return str(self)


class AuthorizationFailure(ConvertorException):
    msg_fmt = _('%(client)s connection failed. Reason: %(reason)s')


class ObjectNotFound(ConvertorException):
    msg_fmt = _("The %(name)s %(id)s could not be found")


class ResourceNotFound(ObjectNotFound):
    msg_fmt = _("The %(name)s resource %(id)s could not be found")
    code = 404


class TaskNotFound(ResourceNotFound):
    msg_fmt = _("Task %(task)s could not be found")


class Conflict(ConvertorException):
    msg_fmt = _('Conflict')
    code = 409


class TaskAlreadyExists(Conflict):
    msg_fmt = _("A task with UUID %(uuid)s already exists")


class Invalid(ConvertorException, ValueError):
    msg_fmt = _("Unacceptable parameters")
    code = HTTPStatus.BAD_REQUEST


class InvalidUUID(Invalid):
    msg_fmt = _("Expected a uuid but received %(uuid)s")


class PatchError(Invalid):
    msg_fmt = _("Couldn't apply patch '%(patch)s'. Reason: %(reason)s")
