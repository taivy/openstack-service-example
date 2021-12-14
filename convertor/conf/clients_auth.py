from keystoneauth1 import loading as ka_loading

WATCHER_CLIENTS_AUTH = 'watcher_clients_auth'


def register_opts(conf):
    ka_loading.register_session_conf_options(conf, WATCHER_CLIENTS_AUTH)
    ka_loading.register_auth_conf_options(conf, WATCHER_CLIENTS_AUTH)


def list_opts():
    return [(WATCHER_CLIENTS_AUTH, ka_loading.get_session_conf_options() +
            ka_loading.get_auth_common_conf_options())]