import os

import alembic
from alembic import config as alembic_config
import alembic.migration as alembic_migration
from oslo_db import exception as db_exc

from convertor._i18n import _
from convertor.db.sqlalchemy import api as sqla_api
from convertor.db.sqlalchemy import models


def _alembic_config():
    path = os.path.join(os.path.dirname(__file__), 'alembic.ini')
    config = alembic_config.Config(path)
    return config


def version(engine=None):
    """Current database version.
    :returns: Database version
    :rtype: string
    """
    if engine is None:
        engine = sqla_api.get_engine()
    with engine.connect() as conn:
        context = alembic_migration.MigrationContext.configure(conn)
        return context.get_current_revision()


def upgrade(revision, config=None):
    """Used for upgrading database.
    :param version: Desired database version
    :type version: string
    """
    revision = revision or 'head'
    config = config or _alembic_config()

    alembic.command.upgrade(config, revision)


def create_schema(config=None, engine=None):
    """Create database schema from models description.
    Can be used for initial installation instead of upgrade('head').
    """
    if engine is None:
        engine = sqla_api.get_engine()

    # NOTE(viktors): If we will use metadata.create_all() for non empty db
    #                schema, it will only add the new tables, but leave
    #                existing as is. So we should avoid of this situation.
    if version(engine=engine) is not None:
        raise db_exc.DBMigrationError(
            _("Convertor database schema is already under version control; "
              "use upgrade() instead"))

    models.Base.metadata.create_all(engine)
    stamp('head', config=config)


def downgrade(revision, config=None):
    """Used for downgrading database.
    :param version: Desired database version
    :type version: string
    """
    revision = revision or 'base'
    config = config or _alembic_config()
    return alembic.command.downgrade(config, revision)


def stamp(revision, config=None):
    """Stamps database with provided revision.
    Don't run any migrations.
    :param revision: Should match one from repository or head - to stamp
                     database with most recent revision
    :type revision: string
    """
    config = config or _alembic_config()
    return alembic.command.stamp(config, revision=revision)


def revision(message=None, autogenerate=False, config=None):
    """Creates template for migration.
    :param message: Text that will be used for migration title
    :type message: string
    :param autogenerate: If True - generates diff based on current database
                         state
    :type autogenerate: bool
    """
    config = config or _alembic_config()
    return alembic.command.revision(config, message=message,
                                    autogenerate=autogenerate)