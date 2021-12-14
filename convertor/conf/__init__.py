from oslo_config import cfg

from convertor.conf import api
from convertor.conf import worker
from convertor.conf import clients_auth
from convertor.conf import db
from convertor.conf import glance_client
from convertor.conf import keystone_client


CONF = cfg.CONF

api.register_opts(CONF)
db.register_opts(CONF)
worker.register_opts(CONF)
glance_client.register_opts(CONF)
keystone_client.register_opts(CONF)
clients_auth.register_opts(CONF)
