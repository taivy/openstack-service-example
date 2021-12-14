from convertor.worker.messaging import trigger
from convertor.common import service_manager

from convertor import conf

CONF = conf.CONF


class WorkerManager(service_manager.ServiceManager):

    @property
    def service_name(self):
        return 'convertor-worker'

    @property
    def api_version(self):
        return '1.0'

    @property
    def publisher_id(self):
        return CONF.convertor_worker.publisher_id

    @property
    def conductor_topic(self):
        return CONF.convertor_worker.conductor_topic

    @property
    def notification_topics(self):
        return []

    @property
    def conductor_endpoints(self):
        return [trigger.TriggerTask]

    @property
    def notification_endpoints(self):
        return []