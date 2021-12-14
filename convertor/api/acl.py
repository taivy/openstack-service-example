"""Access Control Lists (ACL's) control access the API server."""

from convertor.api.middleware import auth_token
from convertor import conf

CONF = conf.CONF


def install(app, conf, public_routes):
    """Install ACL check on application.
    :param app: A WSGI application.
    :param conf: Settings. Dict'ified and passed to keystonemiddleware
    :param public_routes: The list of the routes which will be allowed to
                          access without authentication.
    :return: The same WSGI application with ACL installed.
    """
    if not CONF.get('enable_authentication'):
        return app
    return auth_token.AuthTokenMiddleware(app,
                                          conf=dict(conf.keystone_authtoken),
                                          public_api_routes=public_routes)
