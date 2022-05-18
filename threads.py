from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal

from log import debug


class Worker(QObject):
    finished = pyqtSignal()

    @pyqtSlot()
    def run(self):
        raise NotImplementedError("run() must be implemented by Worker subclasses")

    def finish(self):
        self.finished.emit()

class ThreadsManager(QObject):
    threads = set()
    workers = set()

    def __init__(self):
        super().__init__()



    def start(self, worker: Worker):
        thread_num = f"{len(self.threads)}"
        worker_num = f"{len(self.workers)}"

        thread = QThread()

        self.threads.add(thread)
        self.workers.add(worker)

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)

        @pyqtSlot()
        def release_worker():
            debug("release_worker")
            debug(f"Removing [Worker {worker_num}]")
            self.workers.remove(worker)

        @pyqtSlot()
        def release_thread():
            debug("release_thread")
            debug(f"Removing [Thread {thread_num}]")
            self.threads.remove(thread)

        worker.finished.connect(release_worker)
        worker.finished.connect(worker.deleteLater)

        thread.finished.connect(release_thread)
        thread.finished.connect(thread.deleteLater)

        debug(f"Starting [Worker {worker_num}] in [Thread {thread_num}]")
        thread.start()

_threads_manager = ThreadsManager()

def start(worker: Worker):
    _threads_manager.start(worker)