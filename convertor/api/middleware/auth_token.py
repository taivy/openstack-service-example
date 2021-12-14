import re

from oslo_log import log

from keystonemiddleware import auth_token

from convertor._i18n import _
from convertor.common import exception
from convertor.common import utils

LOG = log.getLogger(__name__)


class AuthTokenMiddleware(auth_token.AuthProtocol):
    """A wrapper on Keystone auth_token middleware.
    Does not perform verification of authentication tokens
    for public routes in the API.
    """
    def __init__(self, app, conf, public_api_routes=()):
        route_pattern_tpl = r'%s(\.json|\.xml)?$'

        try:
            self.public_api_routes = [re.compile(route_pattern_tpl % route_tpl)
                                      for route_tpl in public_api_routes]
        except re.error as e:
            LOG.exception(e)
            raise Exception('Cannot compile public API routes')

        super(AuthTokenMiddleware, self).__init__(app, conf)

    def __call__(self, env, start_response):
        path = utils.safe_rstrip(env.get('PATH_INFO'), '/')

        # The information whether the API call is being performed against the
        # public API is required for some other components. Saving it to the
        # WSGI environment is reasonable thereby.
        env['is_public_api'] = any(re.match(pattern, path)
                                   for pattern in self.public_api_routes)

        if env['is_public_api']:
            return self._app(env, start_response)

        return super(AuthTokenMiddleware, self).__call__(env, start_response)
