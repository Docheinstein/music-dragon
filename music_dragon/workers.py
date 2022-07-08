from typing import Optional, List, Callable, Union

from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal, QMetaObject, Qt

from music_dragon.log import debug
from music_dragon.utils import current_execution_millis

worker_scheduler: Optional['WorkerScheduler'] = None

def initialize(max_num_threads):
    global worker_scheduler
    debug(f"Initializing {max_num_threads} workers")
    worker_scheduler = WorkerScheduler(max_num_threads)


class Worker(QObject):
    # Status

    # The job is in scheduler queue but has not been passed to any thread yet
    STATUS_WAITING = "waiting"

    # The job has been passed (moveToThread) to a thread
    STATUS_DISPATCHED = "dispatched"

    # The job is executing on the thread
    STATUS_RUNNING = "running"

    # The job finished its execution
    STATUS_FINISHED = "finished"

    # Priority
    PRIORITY_IDLE = 5
    PRIORITY_LOW = 10
    PRIORITY_BELOW_NORMAL = 20
    PRIORITY_NORMAL = 30
    PRIORITY_ABOVE_NORMAL = 40
    PRIORITY_HIGH = 50
    PRIORITY_REALTIME = 60

    # Signals
    started = pyqtSignal() # emitted when started
    canceled = pyqtSignal() # emitted when (actually) canceled; could eventually be emitted before started
    finished = pyqtSignal() # emitted when completed (not canceled)

    next_id = 0

    def __init__(self, priority=PRIORITY_NORMAL, tag=None):
        super().__init__()
        self.worker_id = str(Worker.next_id)
        self.tag = tag
        self.priority = priority
        self.status = Worker.STATUS_WAITING
        self.is_canceled = False
        self.born = current_execution_millis()

        Worker.next_id += 1

    @pyqtSlot()
    def exec(self):
        self.status = Worker.STATUS_RUNNING
        self.started.emit()
        self.run()
        self.status = Worker.STATUS_FINISHED
        if self.is_canceled:
            self.canceled.emit()
        else:
            self.finished.emit()

    def run(self):
        raise NotImplementedError("run() must be implemented by Worker subclasses")

    def can_execute(self):
        return True

    def cancel(self):
        debug(f"Cancelling {self}")
        self.is_canceled = True

        # Notify the cancellation only if the worker is not running yet,
        # otherwise do not notify since we cannot stop it actually: it must
        # be handled by the worker's run function instead
        if self.status == Worker.STATUS_RUNNING:
            debug("Note: worker is running: cancel flag must be checked by worker run() itself")
        else:
            self.canceled.emit()

    def __str__(self):
        if self.tag:
            return f"{self.__class__.__name__} {self.worker_id} ({self.tag})"
        return f"{self.__class__.__name__} {self.worker_id}"

    def __lt__(self, other):
        # LIFO: later is better
        return self.born > other.born

        # FIFO: earlier is better
        # return self.born < other.born


class Thread(QThread):
    worker_started = pyqtSignal(str)
    worker_canceled = pyqtSignal(str)
    worker_finished = pyqtSignal(str)

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
        w.started.connect(self._on_worker_started)
        w.canceled.connect(self._on_worker_canceled)
        w.finished.connect(self._on_worker_finished)
        QMetaObject.invokeMethod(w, "exec", Qt.QueuedConnection)


    def active_workers(self):
        return len(self.workers)

    def __str__(self):
        return f"Thread {self.tag}"

    @pyqtSlot()
    def _on_worker_started(self):
        w: Worker = self.sender()
        self.worker_started.emit(w.worker_id)

    @pyqtSlot()
    def _on_worker_canceled(self):
        w: Worker = self.sender()
        try:
            self.workers.pop(w.worker_id)
            debug(f"Removed {w} from {self}: {self.active_workers()} workers now")
        except KeyError:
            print(f"WARN: no worker with id {w.worker_id} among workers of {self}")
        self.worker_canceled.emit(w.worker_id)

    @pyqtSlot()
    def _on_worker_finished(self):
        w: Worker = self.sender()
        try:
            self.workers.pop(w.worker_id)
            debug(f"Removed {w} from {self}: {self.active_workers()} workers now")
        except KeyError:
            print(f"WARN: no worker with id {w.worker_id} among workers of {self}")
        self.worker_finished.emit(w.worker_id)



class WorkerScheduler(QObject):
    POLICY_LIFO = 0
    POLICY_FIFO = 1

    def __init__(self, max_num_threads: int, scheduling_policy=POLICY_LIFO):
        super().__init__()
        self.max_num_threads = max_num_threads
        self.threads: List[Thread] = []
        self.workers = {}
        self.scheduling_policy = scheduling_policy

        debug(f"Initializing WorkerScheduler with {self.max_num_threads} threads")

        for i in range(self.max_num_threads):
            t = Thread(tag=f"{i}")
            t.worker_started.connect(self._on_worker_started)
            t.worker_canceled.connect(self._on_worker_canceled)
            t.worker_finished.connect(self._on_worker_finished)
            self.threads.append(t)

            # TODO: start only when required
            t.start()

    def schedule(self, worker: Worker):
        debug(f"Inserting Worker {worker.worker_id} into the scheduler queue with priority {worker.priority}")

        # Push in the queue or dispatch if possible
        worker.status = Worker.STATUS_WAITING
        self.workers[worker.worker_id] = worker
        self._dispatch_job_while_possible()

    def dispatch(self): # usually not needed since called by schedule
        self._dispatch_job_while_possible()

    def _on_worker_started(self, worker_id):
        pass

    def _on_worker_canceled(self, worker_id):
        self._on_worker_finished(worker_id)

    def _on_worker_finished(self, worker_id):
        # Remove worker
        try:
            w = self.workers.pop(worker_id)
            debug(f"Removed {w} from {self}")
        except KeyError:
            print(f"WARN: no worker with id {worker_id} among workers of {self}")

        # Dispatch next worker if possible
        self._dispatch_job_while_possible()

    def _dispatch_job_while_possible(self):
        while self._dispatch_next_job_if_possible():
            pass

    def _dispatch_next_job_if_possible(self):
        debug("Eventually dispatching next job")

        self._remove_canceled()

        # Dispatch a worker to an available thread, if any is available

        # PRIORITY
        available_thread = self._get_first_available_thread()
        if not available_thread:
            debug("No available thread, not executing job by now")
            return False
        # FIFO
        # available_thread = self._get_most_available_thread()

        debug(f"Available thread found: {available_thread}")

        # Get the job with the highest priority
        # TODO: smarter/faster implementation: priority queue with keys

        # Schedule with the following rules:
        # 1. If a worker has a priority higher than the others, take it
        # 2. Otherwise, aggregate workers of the highest common priority
        #    by class and take the best of each class using the class_scheduling_policy
        # 3. Among the best worker of each class, take the best based on
        #    the scheduler scheduling_policy


        # 1. Figure out the highest priority
        highest_priority = None

        for wid, worker in self.workers.items():
            if worker.status != Worker.STATUS_WAITING:
                continue

            if not worker.can_execute():
                continue

            debug(f"- found dispatchable worker {worker} with priority {worker.priority} born on {worker.born}")
            if highest_priority is None or worker.priority > highest_priority:
                highest_priority = worker.priority

        # 2. Figure out the best worker of each class with this common highest priority
        best_workers_of_classes = {}
        for wid, worker in self.workers.items():
            if worker.status != Worker.STATUS_WAITING:
                continue

            if not worker.can_execute():
                continue

            if worker.priority != highest_priority:
                continue

            worker_class = worker.__class__.__name__
            if worker_class not in best_workers_of_classes:
                best_workers_of_classes[worker_class] = worker
            else:
                if worker < best_workers_of_classes[worker_class]:
                    best_workers_of_classes[worker_class] = worker

        # 3. Figure out the best worker using the scheduler policy
        best_worker = None
        for w in best_workers_of_classes.values():
            if not best_worker:
                best_worker = w
                continue

            if self.scheduling_policy == WorkerScheduler.POLICY_LIFO and w.born > best_worker.born:
                best_worker = w
            elif self.scheduling_policy == WorkerScheduler.POLICY_FIFO and w.born < best_worker.born:
                best_worker = w

        if not best_worker:
            debug("No worker to dispatch")
            return False

        debug(f"Scheduler selected the worker to dispatch: {best_worker} with priority {best_worker.priority} born on {best_worker.born}")

        best_worker.status = Worker.STATUS_DISPATCHED
        available_thread.enqueue_worker(best_worker)
        return True

    def _get_first_available_thread(self) -> Optional[Thread]:
        for t in self.threads:
            if t.active_workers() == 0:
                return t
        return None

    def _get_most_available_thread(self) -> Thread:
        best_thread_idx = 0
        best_thread_num_workers = self.threads[0].active_workers()
        for idx, t in enumerate(self.threads):
            if t.active_workers() < best_thread_num_workers:
                best_thread_num_workers = t.active_workers()
                best_thread_idx = idx
        return self.threads[best_thread_idx]

    def _available_threads(self) -> int:
        return [t.active_workers() for t in self.threads].count(0)

    def _remove_canceled(self):
        canceled_worker_ids = []
        for wid, worker in self.workers.items():
            if worker.is_canceled:
                canceled_worker_ids.append(wid)

        if canceled_worker_ids:
            debug(f"Removing canceled workers: {canceled_worker_ids}")

        for wid in canceled_worker_ids:
            try:
                w = self.workers.pop(wid)
                debug(f"Removed {w} from {self}")
            except KeyError:
                print(f"WARN: no worker with id {wid} among workers of {self}")

    def __str__(self):
        return self.__class__.__name__

def schedule(worker: Worker):
    worker_scheduler.schedule(worker)

def schedule_function(func: Callable, *args, **kwargs):
    class FunctionWorker(Worker):
        def __init__(self, *args_, **kwargs_):
            super().__init__()
            self.args = args_
            self.kwargs = kwargs_

        def run(self):
            func(self.args, self.kwargs)

    worker = FunctionWorker(args, kwargs)
    worker_scheduler.schedule(worker)