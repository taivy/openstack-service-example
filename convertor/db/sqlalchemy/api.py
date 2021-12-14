"""SQLAlchemy storage backend."""

import collections
import datetime
import operator

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_utils import timeutils
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import exc
from sqlalchemy.orm import joinedload

from convertor._i18n import _
from convertor.common import exception
from convertor.common import utils
from convertor.db import api
from convertor.db.sqlalchemy import models
from convertor import objects

CONF = cfg.CONF

_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade.from_config(CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""
    return Connection()


def model_query(model, *args, **kwargs):
    """Query helper for simpler session usage.
    :param session: if present, the session to use
    """
    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


def add_identity_filter(query, value):
    """Adds an identity filter to a query.
    Filters results by ID, if supplied value is a valid integer.
    Otherwise attempts to filter results by UUID.
    :param query: Initial query to add filter to.
    :param value: Value for filtering results by.
    :return: Modified query.
    """
    if utils.is_int_like(value):
        return query.filter_by(id=value)
    elif utils.is_uuid_like(value):
        return query.filter_by(uuid=value)
    else:
        raise exception.InvalidIdentity(identity=value)


def _paginate_query(model, limit=None, marker=None, sort_key=None,
                    sort_dir=None, query=None):
    if not query:
        query = model_query(model)
    sort_keys = ['id']
    if sort_key and sort_key not in sort_keys:
        sort_keys.insert(0, sort_key)
    query = db_utils.paginate_query(query, model, limit, sort_keys,
                                    marker=marker, sort_dir=sort_dir)
    return query.all()

class Connection(api.BaseConnection):
    """SqlAlchemy connection."""

    valid_operators = {
        "": operator.eq,
        "eq": operator.eq,
        "neq": operator.ne,
        "gt": operator.gt,
        "gte": operator.ge,
        "lt": operator.lt,
        "lte": operator.le,
        "in": lambda field, choices: field.in_(choices),
        "notin": lambda field, choices: field.notin_(choices),
    }

    def __init__(self):
        super(Connection, self).__init__()

    def __add_simple_filter(self, query, model, fieldname, value, operator_):
        field = getattr(model, fieldname)

        if (fieldname != 'deleted' and value and
                field.type.python_type is datetime.datetime):
            if not isinstance(value, datetime.datetime):
                value = timeutils.parse_isotime(value)

        return query.filter(self.valid_operators[operator_](field, value))

    def __add_join_filter(self, query, model, fieldname, value, operator_):
        query = query.join(model)
        return self.__add_simple_filter(query, model, fieldname,
                                        value, operator_)

    def __decompose_filter(self, raw_fieldname):
        """Decompose a filter name into its 2 subparts
        A filter can take 2 forms:
        - "<FIELDNAME>" which is a syntactic sugar for "<FIELDNAME>__eq"
        - "<FIELDNAME>__<OPERATOR>" where <OPERATOR> is the comparison operator
          to be used.
        Available operators are:
        - eq
        - neq
        - gt
        - gte
        - lt
        - lte
        - in
        - notin
        """
        separator = '__'
        fieldname, separator, operator_ = raw_fieldname.partition(separator)

        if operator_ and operator_ not in self.valid_operators:
            raise exception.InvalidOperator(
                operator=operator_, valid_operators=self.valid_operators)

        return fieldname, operator_

    def _add_filters(self, query, model, filters=None,
                     plain_fields=None, join_fieldmap=None):
        """Generic way to add filters to a Convertor model
        Each filter key provided by the `filters` parameter will be decomposed
        into 2 pieces: the field name and the comparison operator
        - "": By default, the "eq" is applied if no operator is provided
        - "eq", which stands for "equal" : e.g. {"state__eq": "PENDING"}
          will result in the "WHERE state = 'PENDING'" clause.
        - "neq", which stands for "not equal" : e.g. {"state__neq": "PENDING"}
          will result in the "WHERE state != 'PENDING'" clause.
        - "gt", which stands for "greater than" : e.g.
          {"created_at__gt": "2016-06-06T10:33:22.063176"} will result in the
          "WHERE created_at > '2016-06-06T10:33:22.063176'" clause.
        - "gte", which stands for "greater than or equal to" : e.g.
          {"created_at__gte": "2016-06-06T10:33:22.063176"} will result in the
          "WHERE created_at >= '2016-06-06T10:33:22.063176'" clause.
        - "lt", which stands for "less than" : e.g.
          {"created_at__lt": "2016-06-06T10:33:22.063176"} will result in the
          "WHERE created_at < '2016-06-06T10:33:22.063176'" clause.
        - "lte", which stands for "less than or equal to" : e.g.
          {"created_at__lte": "2016-06-06T10:33:22.063176"} will result in the
          "WHERE created_at <= '2016-06-06T10:33:22.063176'" clause.
        - "in": e.g. {"state__in": ('SUCCEEDED', 'FAILED')} will result in the
          "WHERE state IN ('SUCCEEDED', 'FAILED')" clause.

        :param query: a :py:class:`sqlalchemy.orm.query.Query` instance
        :param model: the model class the filters should relate to
        :param filters: dict with the following structure {"fieldname": value}
        :param plain_fields: a :py:class:`sqlalchemy.orm.query.Query` instance
        :param join_fieldmap: a :py:class:`sqlalchemy.orm.query.Query` instance
        """
        soft_delete_mixin_fields = ['deleted', 'deleted_at']
        timestamp_mixin_fields = ['created_at', 'updated_at']
        filters = filters or {}

        # Special case for 'deleted' because it is a non-boolean flag
        if 'deleted' in filters:
            deleted_filter = filters.pop('deleted')
            op = 'eq' if not bool(deleted_filter) else 'neq'
            filters['deleted__%s' % op] = 0

        plain_fields = tuple(
            (list(plain_fields) or []) +
            soft_delete_mixin_fields +
            timestamp_mixin_fields)
        join_fieldmap = join_fieldmap or {}

        for raw_fieldname, value in filters.items():
            fieldname, operator_ = self.__decompose_filter(raw_fieldname)
            if fieldname in plain_fields:
                query = self.__add_simple_filter(
                    query, model, fieldname, value, operator_)
            elif fieldname in join_fieldmap:
                join_field, join_model = join_fieldmap[fieldname]
                query = self.__add_join_filter(
                    query, join_model, join_field, value, operator_)

        return query

    @staticmethod
    def _get_relationships(model):
        return inspect(model).relationships

    @staticmethod
    def _set_eager_options(model, query):
        relationships = inspect(model).relationships
        for relationship in relationships:
            if not relationship.uselist:
                # We have a One-to-X relationship
                query = query.options(joinedload(relationship.key))
        return query

    def _create(self, model, values):
        obj = model()
        cleaned_values = {k: v for k, v in values.items()
                          if k not in self._get_relationships(model)}
        obj.update(cleaned_values)
        obj.save()
        return obj

    def _get(self, context, model, fieldname, value, eager):
        query = model_query(model)
        if eager:
            query = self._set_eager_options(model, query)

        query = query.filter(getattr(model, fieldname) == value)
        if not context.show_deleted:
            query = query.filter(model.deleted_at.is_(None))

        try:
            obj = query.one()
        except exc.NoResultFound:
            raise exception.ResourceNotFound(name=model.__name__, id=value)

        return obj

    @staticmethod
    def _update(model, id_, values):
        session = get_session()
        with session.begin():
            query = model_query(model, session=session)
            query = add_identity_filter(query, id_)
            try:
                ref = query.with_for_update().one()
            except exc.NoResultFound:
                raise exception.ResourceNotFound(name=model.__name__, id=id_)

            ref.update(values)
        return ref

    @staticmethod
    def _soft_delete(model, id_):
        session = get_session()
        with session.begin():
            query = model_query(model, session=session)
            query = add_identity_filter(query, id_)
            try:
                row = query.one()
            except exc.NoResultFound:
                raise exception.ResourceNotFound(name=model.__name__, id=id_)

            row.soft_delete(session)

            return row

    @staticmethod
    def _destroy(model, id_):
        session = get_session()
        with session.begin():
            query = model_query(model, session=session)
            query = add_identity_filter(query, id_)

            try:
                query.one()
            except exc.NoResultFound:
                raise exception.ResourceNotFound(name=model.__name__, id=id_)

            query.delete()

    def _get_model_list(self, model, add_filters_func, context, filters=None,
                        limit=None, marker=None, sort_key=None, sort_dir=None,
                        eager=False):
        query = model_query(model)
        if eager:
            query = self._set_eager_options(model, query)
        query = add_filters_func(query, filters)
        if not context.show_deleted:
            query = query.filter(model.deleted_at.is_(None))
        return _paginate_query(model, limit, marker,
                               sort_key, sort_dir, query)

    def _add_tasks_filters(self, query, filters):
        if filters is None:
            filters = {}

        plain_fields = ['uuid', 'image_id', 'bucket_id', 'status', 'new_format']

        return self._add_filters(
            query=query, model=models.Task, filters=filters,
            plain_fields=plain_fields)


    # ### GOALS ### #

    def get_task_list(self, *args, **kwargs):
        return self._get_model_list(models.Task,
                                    self._add_tasks_filters,
                                    *args, **kwargs)

    def create_task(self, values):
        # ensure defaults are present for new goals
        if not values.get('uuid'):
            values['uuid'] = utils.generate_uuid()

        try:
            task = self._create(models.Task, values)
        except db_exc.DBDuplicateEntry:
            raise exception.TaskAlreadyExists(uuid=values['uuid'])
        return task

    def _get_task(self, context, fieldname, value, eager):
        try:
            return self._get(context, model=models.Task,
                             fieldname=fieldname, value=value, eager=eager)
        except exception.ResourceNotFound:
            raise exception.TaskNotFound(task=value)

    def get_task_by_id(self, context, task_id, eager=False):
        return self._get_goal(
            context, fieldname="id", value=task_id, eager=eager)

    def get_task_by_uuid(self, context, task_uuid, eager=False):
        return self._get_goal(
            context, fieldname="uuid", value=task_uuid, eager=eager)

    def destroy_goal(self, task_id):
        try:
            return self._destroy(models.Task, task_id)
        except exception.ResourceNotFound:
            raise exception.TaskNotFound(task=task_id)

    def update_goal(self, task_id, values):
        if 'uuid' in values:
            raise exception.Invalid(
                message=_("Cannot overwrite UUID for an existing Task."))

        try:
            return self._update(models.Task, task_id, values)
        except exception.ResourceNotFound:
            raise exception.TaskNotFound(task=task_id)

    def soft_delete_task(self, task_id):
        try:
            return self._soft_delete(models.Task, task_id)
        except exception.ResourceNotFound:
            raise exception.TaskNotFound(task=task_id)