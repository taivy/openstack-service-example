from http import HTTPStatus
import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from convertor.api.controllers import base
from convertor.api.controllers import link
from convertor.api.controllers.v1 import collection
from convertor.api.controllers.v1 import types
from convertor.api.controllers.v1 import utils as api_utils
from convertor.common import exception
from convertor.worker import rpcapi
from convertor import objects


def hide_fields_in_newer_versions(obj):
    """This method hides fields that were added in newer API versions.
    Certain node fields were introduced at certain API versions.
    These fields are only made available when the request's API version
    matches or exceeds the versions when these fields were introduced.
    """
    pass


class TaskPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return []


class Task(base.APIBase):
    """API representation of a task.
    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a task.
    """

    uuid = types.uuid
    """Unique UUID for this task"""

    image_id = wtypes.text

    bucket_id = wtypes.text

    new_format = wtypes.text

    status = wtypes.text

    links = wtypes.wsattr([link.Link], readonly=True)
    """A list containing a self link"""

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Task.fields)

        for k in fields:
            # Skip fields we do not expose.
            if not hasattr(self, k):
                continue
            self.fields.append(k)
            setattr(self, k, kwargs.get(k, wtypes.Unset))

    @staticmethod
    def _convert_with_links(task, url, expand=True):
        if not expand:
            task.unset_fields_except(['uuid', 'image_id', 'bucket_id',
                                      'new_format', 'status'])

        task.links = [link.Link.make_link('self', url,
                                          'tasks', task.uuid),
                      link.Link.make_link('bookmark', url,
                                          'tasks', task.uuid,
                                          bookmark=True)]
        return task

    @classmethod
    def convert_with_links(cls, task, expand=True):
        task = Task(**task.as_dict())
        hide_fields_in_newer_versions(task)
        return cls._convert_with_links(task, pecan.request.host_url, expand)

    @classmethod
    def sample(cls, expand=True):
        sample = cls(
            uuid='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
            image_id='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
            bucket_id='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
            new_format='qcow2',
            status='CREATED'
            )
        return cls._convert_with_links(sample, 'http://localhost:9322', expand)


class TaskCollection(collection.Collection):
    """API representation of a collection of tasks."""

    tasks = [Task]
    """A list containing tasks objects"""

    def __init__(self, **kwargs):
        super(TaskCollection, self).__init__()
        self._type = 'tasks'

    @staticmethod
    def convert_with_links(tasks, limit, url=None, expand=False,
                           **kwargs):
        task_collection = TaskCollection()
        task_collection.tasks = [
            Task.convert_with_links(t, expand) for t in tasks]
        task_collection.next = task_collection.get_next(
            limit, url=url, **kwargs)
        return task_collection

    @classmethod
    def sample(cls):
        sample = cls()
        sample.tasks = [Task.sample(expand=False)]
        return sample


class TasksController(rest.RestController):
    """REST controller for Tasks."""
    def __init__(self):
        super(TasksController, self).__init__()
        self.worker_client = rpcapi.WorkerAPI()

    def _get_tasks_collection(self, marker, limit, sort_key, sort_dir,
                              expand=False, resource_url=None):
        api_utils.validate_sort_key(
            sort_key, list(objects.Task.fields))
        limit = api_utils.validate_limit(limit)
        api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Task.get_by_uuid(
                pecan.request.context, marker)

        sort_db_key = (sort_key if sort_key in objects.Task.fields
                       else None)

        tasks = objects.Task.list(pecan.request.context, limit, marker_obj,
                                  sort_key=sort_db_key, sort_dir=sort_dir)

        return TaskCollection.convert_with_links(tasks, limit,
                                                 url=resource_url,
                                                 expand=expand,
                                                 sort_key=sort_key,
                                                 sort_dir=sort_dir)

    @wsme_pecan.wsexpose(TaskCollection, wtypes.text,
                         int, wtypes.text, wtypes.text)
    def get_all(self, marker=None, limit=None, sort_key='id', sort_dir='asc'):
        """Retrieve a list of tasks.
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        context = pecan.request.context
        #policy.enforce(context, 'task:get_all',
        #               action='task:get_all')
        return self._get_tasks_collection(marker, limit, sort_key, sort_dir)

    @wsme_pecan.wsexpose(Task, wtypes.text)
    def get_one(self, task):
        """Retrieve information about the given task.
        :param task: UUID or name of the task.
        """
        context = pecan.request.context
        rpc_task = api_utils.get_resource('Task', task)
        #policy.enforce(context, 'task:get', rpc_task, action='task:get')

        return Task.convert_with_links(rpc_task)

    @wsme_pecan.wsexpose(Task, body=Task, status_code=HTTPStatus.CREATED)
    def post(self, task):
        """Create a new task.
        :param task: a task within the request body.
        """

        task_dict = task.as_dict()
        context = pecan.request.context
        task_dict['status'] =  objects.task.Status.CREATED
        new_task = objects.Task(context, **task_dict)
        new_task.create()

        # Set the HTTP Location Header
        pecan.response.location = link.build_url('tasks', new_task.uuid)
        self.worker_client.launch_task(pecan.request.context,
                                       new_task.uuid)
        return Task.convert_with_links(new_task)

    @wsme_pecan.wsexpose(None, types.uuid, status_code=HTTPStatus.NO_CONTENT)
    def delete(self, task_uuid):
        """Delete a task.
        :param task_uuid: UUID of a task.
        """
        task_to_delete = objects.Task.get_by_uuid(
            pecan.request.context,
            task_uuid)
        task_to_delete.soft_delete()

    @wsme.validate(types.uuid, [TaskPatchType])
    @wsme_pecan.wsexpose(Task, types.uuid, body=[TaskPatchType])
    def patch(self, task_uuid, patch):
        """Update an existing task.
        :param task_uuid: UUID of a task.
        :param patch: a json PATCH document to apply to this task.
        """
        task_to_update = objects.Task.get_by_uuid(pecan.request.context,
                                                  task_uuid)
        launch_task = False
        try:
            task_dict = task_to_update.as_dict()
            task = Task(**api_utils.apply_jsonpatch(task_dict, patch))
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.Task.fields:
            try:
                patch_val = getattr(task, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if task_to_update[field] != patch_val:
                task_to_update[field] = patch_val

            if (field == 'status' and
                    patch_val == objects.task.Status.INPROGRESS):
                launch_task = True

        task_to_update.save()

        if launch_task:
            self.worker_client.launch_task(pecan.request.context,
                                           task.uuid)

        return Task.convert_with_links(task_to_update)
