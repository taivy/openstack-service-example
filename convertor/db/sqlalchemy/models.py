"""
SQLAlchemy models for convertor service
"""

from oslo_db.sqlalchemy import models
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
import urllib.parse as urlparse
from convertor import conf

CONF = conf.CONF


def table_args():
    engine_name = urlparse.urlparse(CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class ConvertorBase(models.SoftDeleteMixin,
                    models.TimestampMixin, models.ModelBase):
    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    def save(self, session=None):
        import convertor.db.sqlalchemy.api as db_api

        if session is None:
            session = db_api.get_session()

        super(ConvertorBase, self).save(session)


Base = declarative_base(cls=ConvertorBase)


class Task(Base):
    """Represents a task."""

    __tablename__ = 'tasks'
    __table_args__ = (
        UniqueConstraint('uuid', name='uniq_tasks0uuid'),
        table_args(),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    image_id = Column(String(63), nullable=False)
    bucket_id = Column(String(63), nullable=False)
    new_format = Column(String(15), nullable=False)
    status = Column(String(63), nullable=False)
