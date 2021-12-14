from oslo_config import cfg

from glanceclient import client as glclient
from keystoneauth1 import loading as ka_loading
from keystoneclient import client as keyclient

from convertor.common import exception


CONF = cfg.CONF

_CLIENTS_AUTH_GROUP = 'convertor_clients_auth'


class OpenStackClients(object):
    """Convenience class to create and cache client instances."""

    def __init__(self):
        self.reset_clients()

    def reset_clients(self):
        self._session = None
        self._keystone = None
        self._glance = None

    def _get_keystone_session(self):
        auth = ka_loading.load_auth_from_conf_options(CONF,
                                                      _CLIENTS_AUTH_GROUP)
        sess = ka_loading.load_session_from_conf_options(CONF,
                                                         _CLIENTS_AUTH_GROUP,
                                                         auth=auth)
        return sess

    @property
    def auth_url(self):
        return self.keystone().auth_url

    @property
    def session(self):
        if not self._session:
            self._session = self._get_keystone_session()
        return self._session

    def _get_client_option(self, client, option):
        return getattr(getattr(CONF, '%s_client' % client), option)

    @exception.wrap_keystone_exception
    def keystone(self):
        if self._keystone:
            return self._keystone
        keystone_interface = self._get_client_option('keystone',
                                                     'interface')
        keystone_region_name = self._get_client_option('keystone',
                                                       'region_name')
        self._keystone = keyclient.Client(
            interface=keystone_interface,
            region_name=keystone_region_name,
            session=self.session)

        return self._keystone

    @exception.wrap_keystone_exception
    def glance(self):
        if self._glance:
            return self._glance

        glanceclient_version = self._get_client_option('glance', 'api_version')
        glance_endpoint_type = self._get_client_option('glance',
                                                       'endpoint_type')
        glance_region_name = self._get_client_option('glance', 'region_name')
        self._glance = glclient.Client(glanceclient_version,
                                       interface=glance_endpoint_type,
                                       region_name=glance_region_name,
                                       session=self.session)
        return self._glance
