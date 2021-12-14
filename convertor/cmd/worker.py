"""Starter script for the Worker service."""

import os
import sys

from oslo_log import log

from convertor.worker import manager
from convertor.common import service as convertor_service
from convertor import conf

LOG = log.getLogger(__name__)
CONF = conf.CONF


def main():
    convertor_service.prepare_service(sys.argv, CONF)

    LOG.info('Starting Convertor Worker service in PID %s', os.getpid())

    applier_service = convertor_service.Service(manager.WorkerManager)

    # Only 1 process
    launcher = convertor_service.launch(CONF, applier_service)
    launcher.wait()
