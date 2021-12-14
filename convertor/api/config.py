from oslo_config import cfg
from convertor.api import hooks

# Server Specific Configurations
# See https://pecan.readthedocs.org/en/latest/configuration.html#server-configuration # noqa
server = {
    'port': '9322',
    'host': '127.0.0.1'
}

# Pecan Application Configurations
# See https://pecan.readthedocs.org/en/latest/configuration.html#application-configuration # noqa
acl_public_routes = ['/']

app = {
    'root': 'convertor.api.controllers.root.RootController',
    'modules': ['convertor.api'],
    'hooks': [
        hooks.ContextHook(),
    ],
    'static_root': '%(confdir)s/public',
    'enable_acl': True,
    'acl_public_routes': acl_public_routes,
}

# WSME Configurations
# See https://wsme.readthedocs.org/en/latest/integrate.html#configuration
wsme = {
    'debug': cfg.CONF.get("debug") if "debug" in cfg.CONF else False,
}

PECAN_CONFIG = {
    "server": server,
    "app": app,
    "wsme": wsme,
}
