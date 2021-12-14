from oslo_config import cfg

api = cfg.OptGroup(name='api',
                   title='Options for the Watcher API service')

AUTH_OPTS = [
    cfg.BoolOpt('enable_authentication',
                default=True,
                help='This option enables or disables user authentication '
                'via keystone. Default value is True.'),
]

API_SERVICE_OPTS = [
    cfg.PortOpt('port',
                default=9322,
                help='The port for the watcher API server'),
    cfg.HostAddressOpt('host',
                       default='127.0.0.1',
                       help='The listen IP address for the watcher API server'
                       ),
    cfg.IntOpt('max_limit',
               default=1000,
               help='The maximum number of items returned in a single '
                    'response from a collection resource'),
    cfg.IntOpt('workers',
               min=1,
               help='Number of workers for Watcher API service. '
                    'The default is equal to the number of CPUs available '
                    'if that can be determined, else a default worker '
                    'count of 1 is returned.'),

    cfg.BoolOpt('enable_ssl_api',
                default=False,
                help="Enable the integrated stand-alone API to service "
                     "requests via HTTPS instead of HTTP. If there is a "
                     "front-end service performing HTTPS offloading from "
                     "the service, this option should be False; note, you "
                     "will want to change public API endpoint to represent "
                     "SSL termination URL with 'public_endpoint' option."),

    cfg.BoolOpt('enable_webhooks_auth',
                default=True,
                help='This option enables or disables webhook request '
                     'authentication via keystone. Default value is True.'),
]


def register_opts(conf):
    conf.register_group(api)
    conf.register_opts(API_SERVICE_OPTS, group=api)
    conf.register_opts(AUTH_OPTS)


def list_opts():
    return [(api, API_SERVICE_OPTS), ('DEFAULT', AUTH_OPTS)]
