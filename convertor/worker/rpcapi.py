from convertor.common import exception
from convertor.common import service
from convertor.common import service_manager
from convertor.common import utils

from convertor import conf

CONF = conf.CONF


class WorkerAPI(service.Service):

    def __init__(self):
        super(WorkerAPI, self).__init__(WorkerAPIManager)

    def launch_task(self, context, task_uuid=None):
        self.conductor_client.cast(
            context, 'launch_task', task_uuid=task_uuid)


class WorkerAPIManager(service_manager.ServiceManager):

    @property
    def service_name(self):
        return None

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
        return []

    @property
    def notification_endpoints(self):
        return []
