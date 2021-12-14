import futurist

from oslo_config import cfg
from oslo_log import log

from convertor.worker.task import default

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class TriggerTask(object):
    def __init__(self, worker_manager):
        self.worker_manager = worker_manager
        workers = CONF.convertor_worker.workers
        self.executor = futurist.GreenThreadPoolExecutor(max_workers=workers)

    def do_launch_task(self, context, task_uuid):
        try:
            cmd = default.DefaultTaskHandler(context, self.worker_manager, task_uuid)
            cmd.execute()
        except Exception as e:
            LOG.exception(e)

    def launch_action_plan(self, context, task_uuid):
        LOG.debug("Trigger Task %s", task_uuid)
        # submit
        self.executor.submit(self.do_launch_task, context,
                             task_uuid)
        return task_uuid
