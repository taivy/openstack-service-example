from pathlib import Path
import subprocess

from oslo_config import cfg
from oslo_log import log

from convertor.worker import base
from convertor.common import clients
from convertor import objects

LOG = log.getLogger(__name__)
CONF = cfg.CONF


class DefaultWorker(base.BaseWorker):
    def __init__(self, context, worker_manager):
        super(DefaultWorker, self).__init__()
        self._worker_manager = worker_manager
        self._context = context
        self.osc = clients.OpenStackClients()
        self.glance = self.osc.glance()

    @property
    def context(self):
        return self._context

    @property
    def worker_manager(self):
        return self._worker_manager

    def download_image(self, image_id):
        img = self.glance.images.get(image_id)

        file_name = "%s.img" % img.name
        file_path = Path("/tmp/convertor_imgs")
        file_path.mkdir(parents=True, exist_ok=True)
        file_path = file_path / file_name
        full_file_path = file_path.resolve()
        image_file = open(full_file_path, 'w+')

        for chunk in img.data():
            image_file.write(chunk)

        return full_file_path

    def convert_image(self, image_file_path, new_format):
        path_obj = Path(image_file_path)
        new_image_path = path_obj.parent / f"{path_obj.name}.{new_format}"
        subprocess.check_output(["qemu-img", "convert", "-O", new_format, image_file_path, new_image_path])

    def execute(self, task_uuid):
        LOG.debug("Executing task ", task_uuid)
        task = objects.Task.get(self.context, task_uuid)
        image_file_path = self.download_image(task.image_id)
        self.convert_image(image_file_path, task.new_format)
