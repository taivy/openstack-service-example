import importlib
import os
import pkgutil

LIST_OPTS_FUNC_NAME = "list_opts"


def list_opts():
    """Grouped list of all the Watcher-specific configuration options
    :return: A list of ``(group, [opt_1, opt_2])`` tuple pairs, where ``group``
             is either a group name as a string or an OptGroup object.
    """
    opts = list()
    module_names = _list_module_names()
    imported_modules = _import_modules(module_names)
    for mod in imported_modules:
        opts.extend(mod.list_opts())
    return opts


def _list_module_names():
    module_names = []
    package_path = os.path.dirname(os.path.abspath(__file__))
    for __, modname, ispkg in pkgutil.iter_modules(path=[package_path]):
        if modname == "opts" or ispkg:
            continue
        else:
            module_names.append(modname)
    return module_names


def _import_modules(module_names):
    imported_modules = []
    for modname in module_names:
        mod = importlib.import_module("watcher.conf." + modname)
        if not hasattr(mod, LIST_OPTS_FUNC_NAME):
            msg = "The module 'watcher.conf.%s' should have a '%s' "\
                  "function which returns the config options." % \
                  (modname, LIST_OPTS_FUNC_NAME)
            raise Exception(msg)
        else:
            imported_modules.append(mod)
    return imported_modules
