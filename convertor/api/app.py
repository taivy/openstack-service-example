import pecan

from convertor.api import acl
from convertor.api import config as api_config
from convertor import conf

CONF = conf.CONF


def get_pecan_config():
    # Set up the pecan configuration
    return pecan.configuration.conf_from_dict(api_config.PECAN_CONFIG)


def setup_app(config=None):
    if not config:
        config = get_pecan_config()

    app_conf = dict(config.app)

    app = pecan.make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        debug=CONF.debug,
        **app_conf
    )

    return acl.install(app, CONF, config.app.acl_public_routes)


class VersionSelectorApplication(object):
    def __init__(self):
        pc = get_pecan_config()
        self.v1 = setup_app(config=pc)

    def __call__(self, environ, start_response):
        return self.v1(environ, start_response)
