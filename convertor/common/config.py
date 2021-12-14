from oslo_config import cfg

from convertor.common import rpc


def parse_args(argv, default_config_files=None, default_config_dirs=None):
    default_config_files = (default_config_files or
                            cfg.find_config_files(project='convertor'))
    default_config_dirs = (default_config_dirs or
                           cfg.find_config_dirs(project='convertor'))
    rpc.set_defaults(control_exchange='convertor')
    cfg.CONF(argv[1:],
             project='convertor',
             default_config_dirs=default_config_dirs,
             default_config_files=default_config_files)
    rpc.init(cfg.CONF)
