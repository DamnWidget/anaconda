
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import sys
import logging
import threading

import sublime

from .info import Repr
from .localworker import LocalWorker
from .remoteworker import RemoteWorker
#  from .dockerworker import DockerWorker
from .vagrantworker import VagrantWorker
from .helpers import get_settings, active_view

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.WARNING)


class WorkerStore(object, metaclass=Repr):
    """A store of active workers
    """

    __workers = {}
    __lock = threading.RLock()

    @classmethod
    def hire(cls):
        """Hire a new worker of the right type
        """

        worker = None
        view = active_view()
        python = get_settings(view, 'python_interpreter', 'python')
        if python.startswith('tcp://'):
            worker = RemoteWorker()
        elif python.startswith('vagrant:'):
            if get_settings(view, 'vagrant_environment') is None:
                logger.error(
                    'The configured interpreter is set to vagrant: {} '
                    'but there is no vagrant configuration.'
                )
            else:
                worker = VagrantWorker()
        #  elif python.startswith('docker:'):
            #  if get_settings(view, 'docker_environment') is None:
                #  logger.error(
                #      'The configured interpreter is set to docker: {} '
                #       'but there is no docker configuration.'
                #  )
            #  else:
                #  worker = DockerWorker()
        else:
            worker = LocalWorker()

        return worker

    @classmethod
    def add(cls, window_id, worker):
        """Add a new worker to the workers store
        """

        with cls.__lock:
            if cls.__workers.get(window_id) is None:
                cls.__workers[window_id] = worker
            else:
                logging.warning(
                    'In worker.WorkerStore.append: tried to append an '
                    'existent worker for window {} to the workers '
                    'store. Skypping.'.format(window_id)
                )

    @classmethod
    def get(cls, window_id):
        """Retrieve a worker for the given window_id from the workers store
        """

        worker = None
        with cls.__lock:
            worker = cls.__workers.get(window_id, worker)

        return worker

    @classmethod
    def remove(cls, window_id):
        """Remove a worker from the workers store
        """

        worker = cls.__workers.pop(window_id, None)
        if worker is None:
            logging.error(
                'In worker.WorkerStore.remove: tried to remove a worker '
                'that is not part of the workers store for window '
                '{}. Skipping.'.format(window_id)
            )
            return

        # stop the worker using it's own implementation
        worker.stop()

    @classmethod
    def execute(cls, callback, **data):
        """Execute the given method remotely and call the callback with result
        """

        window_id = sublime.active_window().id()
        worker = WorkerStore.get(window_id)
        if worker is None:
            # hire a new worker
            worker = WorkerStore.hire()
            if worker is None:
                # problems in the configuration probably
                return
            WorkerStore.add(window_id, worker)

        if worker.client is not None:
            if not worker.client.connected:
                worker.reconnecting = True
                worker.start()
            else:
                worker._execute(callback, **data)
        else:
            worker.start()

    @classmethod
    def _repr(cls):
        """Return a representation of the WorkerStore
        """

        workers_data = []
        for window_id, worker in cls.__workers.items():
            workers_data.append('Window ID: {}\n{}'.format(window_id, worker))

        return '{} workers in the store\n\n{}'.format(
            len(cls.__workers), '\n\n'.join(workers_data)
        )
