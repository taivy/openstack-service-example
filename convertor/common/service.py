import socket

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import _options
from oslo_log import log
import oslo_messaging as messaging
from oslo_reports import opts as gmr_opts
from oslo_service import service
from oslo_service import wsgi

from convertor._i18n import _
from convertor.api import app
from convertor.common import config
from convertor.common import rpc
from convertor import objects
from convertor.objects import base
from convertor.objects import fields as wfields


NOTIFICATION_OPTS = [
    cfg.StrOpt('notification_level',
               choices=[''] + list(wfields.NotificationPriority.ALL),
               default=wfields.NotificationPriority.INFO,
               help=_('Specifies the minimum level for which to send '
                      'notifications. If not set, no notifications will '
                      'be sent. The default is for this option to be at the '
                      '`INFO` level.'))
]
cfg.CONF.register_opts(NOTIFICATION_OPTS)


CONF = cfg.CONF
LOG = log.getLogger(__name__)

_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN', 'qpid.messaging=INFO',
                       'oslo.messaging=INFO', 'sqlalchemy=WARN',
                       'keystoneclient=INFO', 'stevedore=INFO',
                       'eventlet.wsgi.server=WARN', 'iso8601=WARN',
                       'requests=WARN', 'neutronclient=WARN',
                       'glanceclient=WARN',
                       'apscheduler=WARN']

Singleton = service.Singleton


class WSGIService(service.ServiceBase):
    """Provides ability to launch Watcher API from wsgi app."""

    def __init__(self, service_name, use_ssl=False):
        """Initialize, but do not start the WSGI server.
        :param service_name: The service name of the WSGI server.
        :param use_ssl: Wraps the socket in an SSL context if True.
        """
        self.service_name = service_name
        self.app = app.VersionSelectorApplication()
        self.workers = (CONF.api.workers or
                        processutils.get_worker_count())
        self.server = wsgi.Server(CONF, self.service_name, self.app,
                                  host=CONF.api.host,
                                  port=CONF.api.port,
                                  use_ssl=use_ssl,
                                  logger_name=self.service_name)

    def start(self):
        """Start serving this service using loaded configuration"""
        self.server.start()

    def stop(self):
        """Stop serving this API"""
        self.server.stop()

    def wait(self):
        """Wait for the service to stop serving this API"""
        self.server.wait()

    def reset(self):
        """Reset server greenpool size to default"""
        self.server.reset()


class Service(service.ServiceBase):

    API_VERSION = '1.0'

    def __init__(self, manager_class):
        super(Service, self).__init__()
        self.manager = manager_class()

        self.publisher_id = self.manager.publisher_id
        self.api_version = self.manager.api_version

        self.conductor_topic = self.manager.conductor_topic
        self.notification_topics = self.manager.notification_topics

        self.heartbeat = None

        self.service_name = self.manager.service_name
        if self.service_name:
            '''
            self.heartbeat = ServiceHeartbeat(
                service_name=self.manager.service_name)
            '''
            pass

        self.conductor_endpoints = [
            ep(self) for ep in self.manager.conductor_endpoints
        ]
        self.notification_endpoints = self.manager.notification_endpoints

        self._conductor_client = None

        self.conductor_topic_handler = None
        self.notification_handler = None

        if self.conductor_topic and self.conductor_endpoints:
            self.conductor_topic_handler = self.build_topic_handler(
                self.conductor_topic, self.conductor_endpoints)
        if self.notification_topics and self.notification_endpoints:
            self.notification_handler = self.build_notification_handler(
                self.notification_topics, self.notification_endpoints
            )

    @property
    def conductor_client(self):
        if self._conductor_client is None:
            target = messaging.Target(
                topic=self.conductor_topic,
                version=self.API_VERSION,
            )
            self._conductor_client = rpc.get_client(
                target,
                serializer=base.WatcherObjectSerializer()
            )
        return self._conductor_client

    @conductor_client.setter
    def conductor_client(self, c):
        self.conductor_client = c

    def build_topic_handler(self, topic_name, endpoints=()):
        target = messaging.Target(
            topic=topic_name,
            # For compatibility, we can override it with 'host' opt
            server=CONF.host or socket.gethostname(),
            version=self.api_version,
        )
        return rpc.get_server(
            target, endpoints,
            serializer=rpc.JsonPayloadSerializer()
        )

    def build_notification_handler(self, topic_names, endpoints=()):
        targets = []
        for topic in topic_names:
            kwargs = {}
            if '.' in topic:
                exchange, topic = topic.split('.')
                kwargs['exchange'] = exchange
            kwargs['topic'] = topic
            targets.append(messaging.Target(**kwargs))

        return rpc.get_notification_listener(
            targets, endpoints,
            serializer=rpc.JsonPayloadSerializer(),
            pool=CONF.host
        )

    def start(self):
        LOG.debug("Connecting to '%s'", CONF.transport_url)
        if self.conductor_topic_handler:
            self.conductor_topic_handler.start()
        if self.notification_handler:
            self.notification_handler.start()
        if self.heartbeat:
            self.heartbeat.start()

    def stop(self):
        LOG.debug("Disconnecting from '%s'", CONF.transport_url)
        if self.conductor_topic_handler:
            self.conductor_topic_handler.stop()
        if self.notification_handler:
            self.notification_handler.stop()
        if self.heartbeat:
            self.heartbeat.stop()

    def reset(self):
        """Reset a service in case it received a SIGHUP."""

    def wait(self):
        """Wait for service to complete."""


def launch(conf, service_, workers=1, restart_method='mutate'):
    return service.launch(conf, service_, workers, restart_method)


def prepare_service(argv=(), conf=cfg.CONF):
    log.register_options(conf)
    gmr_opts.set_defaults(conf)

    config.parse_args(argv)
    cfg.set_defaults(_options.log_opts,
                     default_log_levels=_DEFAULT_LOG_LEVELS)
    log.setup(conf, 'python-convertor')
    conf.log_opt_values(LOG, log.DEBUG)
    objects.register_all()
