import sys

from oslo_config import cfg
import oslo_i18n as i18n
from oslo_log import log

from convertor.api import app
from convertor.common import service


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def initialize_wsgi_app(show_deprecated=False):
    i18n.install('convertor')

    service.prepare_service(sys.argv)

    LOG.debug("Configuration:")
    CONF.log_opt_values(LOG, log.DEBUG)

    return app.VersionSelectorApplication()
