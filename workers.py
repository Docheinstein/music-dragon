from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal, QMetaObject, Qt

from log import debug


_worker_dispatcher: Optional['WorkerDispatcher'] = None

def initialize():
    global _worker_dispatcher
    _worker_dispatcher = WorkerDispatcher()

class Worker(QObject):
    next_id = 0

    finished = pyqtSignal()

    def __init__(self, tag=None):
        super().__init__()
        self.worker_id = Worker.next_id
        Worker.next_id += 1
        self.tag = tag

    @pyqtSlot()
    def run(self):
        raise NotImplementedError("run() must be implemented by Worker subclasses")

    def finish(self):
        self.finished.emit()

    def __str__(self):
        if self.tag:
            return f"Worker {self.worker_id} ({self.tag})"
        return f"Worker {self.worker_id}"

class Thread(QThread):
    def __init__(self, tag=None):
        super().__init__()
        self.tag = tag
        self.workers = {}

    def start(self, priority=QThread.InheritPriority) -> None:
        super().start(priority)
        debug(f"Started {self}")

    def enqueue_worker(self, w: Worker):
        self.workers[w.worker_id] = w
        debug(f"Enqueued {w} to {self}: {self.active_workers()} workers now")
        w.moveToThread(self)
        w.finished.connect(self._on_worker_finished)
        QMetaObject.invokeMethod(w, "run", Qt.QueuedConnection)


    def active_workers(self):
        return len(self.workers)

    def __str__(self):
        return f"Thread {self.tag}"

    @pyqtSlot()
    def _on_worker_finished(self):
        w: Worker = self.sender()
        try:
            self.workers.pop(w.worker_id)
            debug(f"Removed {w} from {self}: {self.active_workers()} workers now")
        except KeyError:
            print(f"WARN: no worker with id {w.worker_id} among workers of {self}")


class WorkerDispatcher(QObject):

    def __init__(self, max_num_threads=QThread.idealThreadCount()):
        super().__init__()
        self.max_num_threads = max_num_threads
        self.threads = []

        debug(f"Initializing WorkerDispatcher with {self.max_num_threads} threads")

        for i in range(self.max_num_threads):
            t = Thread(tag=f"{i}")
            self.threads.append(t)

            # TODO: start only when required
            t.start()


    def execute(self, worker: Worker):
        # Find the thread with the lower number of active workers
        debug(f"Going to dispatch {worker}, choosing which thread will execute it")
        best_thread_idx = 0
        best_thread_num_workers = self.threads[0].active_workers()
        for idx, t in enumerate(self.threads):
            if t.active_workers() < best_thread_num_workers:
                best_thread_num_workers = t.active_workers()
                best_thread_idx = idx

        best_thread = self.threads[best_thread_idx]
        debug(f"Executing {worker} on {best_thread}")
        best_thread.enqueue_worker(worker)


def execute(worker: Worker):
    _worker_dispatcher.execute(worker)