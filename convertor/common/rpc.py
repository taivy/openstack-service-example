from oslo_config import cfg
from oslo_log import log
import oslo_messaging as messaging

from oslo_messaging.rpc import dispatcher

from convertor.common import context as watcher_context
from convertor.common import exception

__all__ = [
    'init',
    'cleanup',
    'set_defaults',
    'add_extra_exmods',
    'clear_extra_exmods',
    'get_allowed_exmods',
    'RequestContextSerializer',
    'get_client',
    'get_server',
    'get_notifier',
]

CONF = cfg.CONF
LOG = log.getLogger(__name__)
TRANSPORT = None
NOTIFICATION_TRANSPORT = None
NOTIFIER = None

ALLOWED_EXMODS = [
    exception.__name__,
]
EXTRA_EXMODS = []


JsonPayloadSerializer = messaging.JsonPayloadSerializer


def init(conf):
    global TRANSPORT, NOTIFICATION_TRANSPORT, NOTIFIER
    exmods = get_allowed_exmods()
    TRANSPORT = messaging.get_rpc_transport(
        conf, allowed_remote_exmods=exmods)
    NOTIFICATION_TRANSPORT = messaging.get_notification_transport(
        conf, allowed_remote_exmods=exmods)

    serializer = RequestContextSerializer(JsonPayloadSerializer())
    if not conf.notification_level:
        NOTIFIER = messaging.Notifier(
            NOTIFICATION_TRANSPORT, serializer=serializer, driver='noop')
    else:
        NOTIFIER = messaging.Notifier(NOTIFICATION_TRANSPORT,
                                      serializer=serializer)


def initialized():
    return None not in [TRANSPORT, NOTIFIER]


def cleanup():
    global TRANSPORT, NOTIFICATION_TRANSPORT, NOTIFIER
    if NOTIFIER is None:
        LOG.exception("RPC cleanup: NOTIFIER is None")
    TRANSPORT.cleanup()
    NOTIFICATION_TRANSPORT.cleanup()
    TRANSPORT = NOTIFICATION_TRANSPORT = NOTIFIER = None


def set_defaults(control_exchange):
    messaging.set_transport_defaults(control_exchange)


def add_extra_exmods(*args):
    EXTRA_EXMODS.extend(args)


def clear_extra_exmods():
    del EXTRA_EXMODS[:]


def get_allowed_exmods():
    return ALLOWED_EXMODS + EXTRA_EXMODS


class RequestContextSerializer(messaging.Serializer):

    def __init__(self, base):
        self._base = base

    def serialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.serialize_entity(context, entity)

    def deserialize_entity(self, context, entity):
        if not self._base:
            return entity
        return self._base.deserialize_entity(context, entity)

    def serialize_context(self, context):
        return context.to_dict()

    def deserialize_context(self, context):
        return watcher_context.RequestContext.from_dict(context)


def get_client(target, version_cap=None, serializer=None):
    assert TRANSPORT is not None
    serializer = RequestContextSerializer(serializer)
    return messaging.RPCClient(
        TRANSPORT,
        target,
        version_cap=version_cap,
        serializer=serializer
    )


def get_server(target, endpoints, serializer=None):
    assert TRANSPORT is not None
    access_policy = dispatcher.DefaultRPCAccessPolicy
    serializer = RequestContextSerializer(serializer)
    return messaging.get_rpc_server(
        TRANSPORT,
        target,
        endpoints,
        executor='eventlet',
        serializer=serializer,
        access_policy=access_policy
    )


def get_notification_listener(targets, endpoints, serializer=None, pool=None):
    assert NOTIFICATION_TRANSPORT is not None
    serializer = RequestContextSerializer(serializer)
    return messaging.get_notification_listener(
        NOTIFICATION_TRANSPORT,
        targets,
        endpoints,
        allow_requeue=False,
        executor='eventlet',
        pool=pool,
        serializer=serializer
    )


def get_notifier(publisher_id):
    assert NOTIFIER is not None
    return NOTIFIER.prepare(publisher_id=publisher_id)
