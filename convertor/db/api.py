"""
Base classes for storage engines
"""

import abc
from oslo_config import cfg
from oslo_db import api as db_api

_BACKEND_MAPPING = {'sqlalchemy': 'convertor.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF, backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def get_instance():
    """Return a DB API instance."""
    return IMPL


class BaseConnection(object, metaclass=abc.ABCMeta):
    """Base class for storage system connections."""

    @abc.abstractmethod
    def get_task_list(self, context, filters=None, limit=None,
                      marker=None, sort_key=None, sort_dir=None):
        """Get specific columns for matching tasks.

        Return a list of the specified columns for all goals that
        match the specified filters.

        :param context: The security context
        :param filters: Filters to apply. Defaults to None.
        :param limit: Maximum number of tasks to return.
        :param marker: the last item of the previous page; we return the next
                       result set.
        :param sort_key: Attribute by which results should be sorted.
        :param sort_dir: direction in which results should be sorted.
                         (asc, desc)
        :returns: A list of tuples of the specified columns.
        """

    @abc.abstractmethod
    def create_task(self, values):
        """Create a new task.

        :param values: A dict
        :returns: A task
        """

    @abc.abstractmethod
    def get_task_by_id(self, context, task_id, eager=False):
        """Return a task given its ID.

        :param context: The security context
        :param task_id: The ID of a goal
        :param eager: If True, also loads One-to-X data (Default: False)
        :returns: A task
        :raises: :py:class:`~.TaskNotFound`
        """

    @abc.abstractmethod
    def get_task_by_uuid(self, context, task_uuid, eager=False):
        """Return a goal given its UUID.

        :param context: The security context
        :param task_uuid: The UUID of a goal
        :param eager: If True, also loads One-to-X data (Default: False)
        :returns: A task
        :raises: :py:class:`~.TaskNotFound`
        """

    @abc.abstractmethod
    def destroy_task(self, task_uuid):
        """Destroy a goal.

        :param task_uuid: The UUID of a goal
        :raises: :py:class:`~.TaskNotFound`
        """

    @abc.abstractmethod
    def update_task(self, task_uuid, values):
        """Update properties of a task.

        :param task_uuid: The UUID of a task
        :param values: A dict
        :returns: A task
        :raises: :py:class:`~.TaskNotFound`
        :raises: :py:class:`~.Invalid`
        """

    def soft_delete_task(self, task_id):
        """Soft delete a task.

        :param task_id: The id or uuid of a task.
        :raises: :py:class:`~.TaskNotFound`
        """
