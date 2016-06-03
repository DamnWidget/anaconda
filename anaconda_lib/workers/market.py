
# Copyright (C) 2013 - 2016 - Oscar Campos <oscar.campos@member.fsf.org>
# This program is Free Software see LICENSE file for details

import threading

import sublime

from ..info import Repr
from ..logger import Log
from ..constants import WorkerStatus
from .interpreter import Interpreter
from .local_worker import LocalWorker
from .remote_worker import RemoteWorker
from .vagrant_worker import VagrantWorker
from ..helpers import active_view, get_interpreter


class Market(object, metaclass=Repr):
    """When you need a worker you hire one in the market
    """

    _worker_pool = {}
    _lock = threading.RLock()
    _workers_type = {'tcp': RemoteWorker, 'vagrant': VagrantWorker}

    def hire(self):
        """Hire the right worker from the market pool
        """

        raw_interpreter = get_interpreter(active_view())
        itprt = Interpreter(raw_interpreter)
        return self._workers_type.get(itprt.scheme, LocalWorker)(itprt)

    def add(self, window_id, worker):
        """Add the given worker into the workers pool
        """

        with self._lock:
            if self._worker_pool.get(window_id) is None:
                self._worker_pool[window_id] = worker
            else:
                Log.warning(
                    'tried to append an existent worker for window {} to '
                    'the workers market. Skipping...'.format(window_id)
                )

    def get(self, window_id):
        """Retrieve a worker for the given window_id from the workers market
        """

        with self._lock:
            worker = self._worker_pool.get(window_id)

        return worker

    def fire(self, window_id):
        """Remote a worker from the workers market
        """

        worker = self._worker_pool.pop(window_id, None)
        if worker is None:
            Log.error(
                'tried to remove a worker that is not part of the workers '
                'market for window {}. Skipping'.format(window_id)
            )
            return

    @classmethod
    def execute(cls, callback, **data):
        """Execute the given method remotely and call the callback with result
        """

        def _start_worker(wk, cb, **d):
            wk.start()
            if wk.status == WorkerStatus.healthy:
                wk._execute(cb, **d)
                return

            sublime.set_timeout_async(lambda: _start_worker(wk, cb, **d), 5000)

        window_id = sublime.active_window().id()
        worker = cls.get(cls, window_id)
        if worker is None:
            # hire a new worker
            worker = cls.hire(cls)
            cls.add(cls, window_id, worker)

        if worker.status == WorkerStatus.faulty:
            return

        if worker.status == WorkerStatus.quiting:
            cls.fire(cls, window_id)
            return

        if worker.client is not None:
            if not worker.client.connected:
                worker.reconnecting = True
                worker.state = WorkerStatus.incomplete
                _start_worker(worker, callback, **data)
            else:
                worker._append_context_data(data)
                worker._execute(callback, **data)
                if worker.status == WorkerStatus.quiting:
                    # that means that we need to let the worker go
                    cls.fire(cls, window_id)
        else:
            _start_worker(worker, callback, **data)

    @classmethod
    def lookup(cls, window_id):
        """Alias for get
        """

        return cls.get(cls, window_id)

    @classmethod
    def _repr(cls):
        """Returns a representation of the Market
        """

        workers_data = []
        for window_id, worker in cls._worker_pool.items():
            workers_data.append('Window ID: {}\n{}'.format(window_id, worker))

        return '{} workers in the market\n\n{}'.format(
            len(cls._worker_pool), '\n\n'.join(workers_data)
        )
