import sys

from oslo_config import cfg
from oslo_log import log

from convertor.common import service
from convertor import conf

LOG = log.getLogger(__name__)
CONF = conf.CONF


def main():
    service.prepare_service(sys.argv, CONF)

    host, port = cfg.CONF.api.host, cfg.CONF.api.port
    protocol = "http" if not CONF.api.enable_ssl_api else "https"
    # Build and start the WSGI app
    server = service.WSGIService('convertor-api', CONF.api.enable_ssl_api)

    if host == '127.0.0.1':
        LOG.info('serving on 127.0.0.1:%(port)s, '
                 'view at %(protocol)s://127.0.0.1:%(port)s',
                 dict(protocol=protocol, port=port))
    else:
        LOG.info('serving on %(protocol)s://%(host)s:%(port)s',
                 dict(protocol=protocol, host=host, port=port))

    launcher = service.launch(CONF, server, workers=server.workers)
    launcher.wait()
