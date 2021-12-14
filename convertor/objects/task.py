from convertor.common import exception
from watcher.common import utils
from convertor.db import api as db_api
from convertor.objects import base
from convertor.objects import fields as wfields


class Status(object):
    CREATED = 'CREATED'
    INPROGRESS = 'INPROGRESS'
    COMPLETED = 'COMPLETED'
    ERROR = 'ERROR'
    DELETED = 'DELETED'


@base.ConvertorObjectRegistry.register
class Task(base.ConvertorPersistentObject, base.ConvertorObject,
           base.ConvertorObjectDictCompat):
    # Version 1.0: Initial version
    VERSION = '1.0'

    dbapi = db_api.get_instance()

    fields = {
        'id': wfields.IntegerField(),
        'uuid': wfields.UUIDField(),
        'image_id': wfields.StringField(),
        'bucket_id': wfields.StringField(),
        'new_format': wfields.StringField(),
        'status': wfields.StringField(nullable=True),
    }

    @base.remotable_classmethod
    def get(cls, context, task_id):
        """Find a task based on its id or uuid
        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Goal(context)
        :param task_id: the id *or* uuid of a task.
        :returns: a :class:`Task` object.
        """
        if utils.is_int_like(task_id):
            return cls.get_by_id(context, task_id)
        elif utils.is_uuid_like(task_id):
            return cls.get_by_uuid(context, task_id)
        else:
            raise exception.InvalidIdentity(identity=task_id)

    @base.remotable_classmethod
    def get_by_id(cls, context, task_id):
        """Find a task based on its integer id
        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Task(context)
        :param task_id: the id *or* uuid of a task.
        :returns: a :class:`Task` object.
        """
        db_task = cls.dbapi.get_task_by_id(context, task_id)
        task = cls._from_db_object(cls(context), db_task)
        return task

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        """Find a goal based on uuid
        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Goal(context)
        :param uuid: the uuid of a goal.
        :returns: a :class:`Goal` object.
        """
        db_task = cls.dbapi.get_task_by_uuid(context, uuid)
        task = cls._from_db_object(cls(context), db_task)
        return task

    @base.remotable_classmethod
    def list(cls, context, limit=None, marker=None, filters=None,
             sort_key=None, sort_dir=None):
        """Return a list of :class:`Task` objects.
        :param context: Security context. NOTE: This should only
                        be used internally by the indirection_api.
                        Unfortunately, RPC requires context as the first
                        argument, even though we don't use it.
                        A context should be set when instantiating the
                        object, e.g.: Goal(context)
        :param filters: dict mapping the filter key to a value.
        :param limit: maximum number of resources to return in a single result.
        :param marker: pagination marker for large data sets.
        :param sort_key: column to sort results by.
        :param sort_dir: direction to sort. "asc" or "desc".
        :returns: a list of :class:`Task` object.
        """
        db_tasks = cls.dbapi.get_task_list(
            context,
            filters=filters,
            limit=limit,
            marker=marker,
            sort_key=sort_key,
            sort_dir=sort_dir)

        return [cls._from_db_object(cls(context), obj) for obj in db_tasks]

    @base.remotable
    def create(self):
        """Create a :class:`Task` record in the DB"""
        values = self.obj_get_changes()
        db_task = self.dbapi.create_task(values)
        self._from_db_object(self, db_task)

    def destroy(self):
        """Delete the :class:`Task` from the DB"""
        self.dbapi.destroy_task(self.id)
        self.obj_reset_changes()

    @base.remotable
    def save(self):
        """Save updates to this :class:`Task`.
        Updates will be made column by column based on the result
        of self.what_changed().
        """
        updates = self.obj_get_changes()
        db_obj = self.dbapi.update_task(self.uuid, updates)
        obj = self._from_db_object(self, db_obj, eager=False)
        self.obj_refresh(obj)
        self.obj_reset_changes()

    @base.remotable
    def refresh(self):
        """Loads updates for this :class:`Task`.
        Loads a goal with the same uuid from the database and
        checks for updated attributes. Updates are applied from
        the loaded goal column by column, if there are any updates.
        """
        current = self.get_by_uuid(self._context, uuid=self.uuid)
        self.obj_refresh(current)

    @base.remotable
    def soft_delete(self):
        """Soft Delete the :class:`Task` from the DB"""
        self.status = Status.DELETED
        self.save()
        db_obj = self.dbapi.soft_delete_task(self.uuid)
        obj = self._from_db_object(
            self.__class__(self._context), db_obj, eager=False)
        self.obj_refresh(obj)