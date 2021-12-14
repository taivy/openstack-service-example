from oslo_config import cfg

watcher_applier = cfg.OptGroup(name='watcher_applier',
                               title='Options for the Applier messaging '
                               'core')

APPLIER_MANAGER_OPTS = [
    cfg.IntOpt('workers',
               default=1,
               min=1,
               required=True,
               help='Number of workers for applier, default value is 1.'),
    cfg.StrOpt('conductor_topic',
               default='convertor.worker.control',
               help='The topic name used for '
                    'control events, this topic '
                    'used for rpc call '),
    cfg.StrOpt('publisher_id',
               default='convertor.worker.api',
               help='The identifier used by watcher '
                    'module on the message broker'),
    cfg.StrOpt('workflow_engine',
               default='taskflow',
               required=True,
               help='Select the engine to use to execute the workflow'),
]


def register_opts(conf):
    conf.register_group(watcher_applier)
    conf.register_opts(APPLIER_MANAGER_OPTS, group=watcher_applier)


def list_opts():
    return [(watcher_applier, APPLIER_MANAGER_OPTS)]
