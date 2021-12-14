"""
Run storage database migration.
"""

import sys

from oslo_config import cfg

from convertor.common import service
from convertor import conf
from convertor.db import migration

CONF = conf.CONF


class DBCommand(object):

    @staticmethod
    def upgrade():
        migration.upgrade(CONF.command.revision)

    @staticmethod
    def downgrade():
        migration.downgrade(CONF.command.revision)

    @staticmethod
    def revision():
        migration.revision(CONF.command.message, CONF.command.autogenerate)

    @staticmethod
    def stamp():
        migration.stamp(CONF.command.revision)

    @staticmethod
    def version():
        print(migration.version())

    @staticmethod
    def create_schema():
        migration.create_schema()


def add_command_parsers(subparsers):
    parser = subparsers.add_parser(
        'upgrade',
        help="Upgrade the database schema to the latest version. "
             "Optionally, use --revision to specify an alembic revision "
             "string to upgrade to.")
    parser.set_defaults(func=DBCommand.upgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser(
        'downgrade',
        help="Downgrade the database schema to the oldest revision. "
             "While optional, one should generally use --revision to "
             "specify the alembic revision string to downgrade to.")
    parser.set_defaults(func=DBCommand.downgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser('stamp')
    parser.add_argument('revision', nargs='?')
    parser.set_defaults(func=DBCommand.stamp)

    parser = subparsers.add_parser(
        'revision',
        help="Create a new alembic revision. "
             "Use --message to set the message string.")
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.set_defaults(func=DBCommand.revision)

    parser = subparsers.add_parser(
        'version',
        help="Print the current version information and exit.")
    parser.set_defaults(func=DBCommand.version)

    parser = subparsers.add_parser(
        'create_schema',
        help="Create the database schema.")
    parser.set_defaults(func=DBCommand.create_schema)



command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Available commands',
                                handler=add_command_parsers)


def register_sub_command_opts():
    cfg.CONF.register_cli_opt(command_opt)


def main():
    register_sub_command_opts()
    # this is hack to work with previous usage of watcher-dbsync
    # pls change it to watcher-dbsync upgrade
    valid_commands = set([
        'upgrade', 'downgrade', 'revision',
        'version', 'stamp', 'create_schema'
    ])
    if not set(sys.argv).intersection(valid_commands):
        sys.argv.append('upgrade')

    service.prepare_service(sys.argv, CONF)
    CONF.command.func()