from oslo_config import cfg

keystone_client = cfg.OptGroup(name='keystone_client',
                               title='Configuration Options for Keystone')

KEYSTONE_CLIENT_OPTS = [
    cfg.StrOpt('interface',
               default='admin',
               choices=['internal', 'public', 'admin'],
               help='Type of endpoint to use in keystoneclient.'),
    cfg.StrOpt('region_name',
               help='Region in Identity service catalog to use for '
                    'communication with the OpenStack service.')]


def register_opts(conf):
    conf.register_group(keystone_client)
    conf.register_opts(KEYSTONE_CLIENT_OPTS, group=keystone_client)


def list_opts():
    return [(keystone_client, KEYSTONE_CLIENT_OPTS)]
