from typing import Optional, List

from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal, QMetaObject, Qt

from log import debug
from utils import current_millis

_worker_scheduler: Optional['WorkerScheduler'] = None

def initialize(max_num_threads):
    global _worker_scheduler
    debug(f"Initializing {max_num_threads} workers")
    _worker_scheduler = WorkerScheduler(max_num_threads)


class Worker(QObject):
    next_id = 0

    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, tag=None):
        super().__init__()
        self.worker_id = str(Worker.next_id)
        Worker.next_id += 1
        self.tag = tag

    def run(self):
        raise NotImplementedError("run() must be implemented by Worker subclasses")

    @pyqtSlot()
    def exec(self):
        self.started.emit()
        self.run()
        self.finished.emit()

    def can_execute(self):
        return True

    def is_canceled(self):
        return False

    def __str__(self):
        if self.tag:
            return f"Worker {self.worker_id} ({self.tag})"
        return f"Worker {self.worker_id}"


class Thread(QThread):
    worker_started = pyqtSignal(str)
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
    def _on_worker_finished(self):
        w: Worker = self.sender()
        try:
            self.workers.pop(w.worker_id)
            debug(f"Removed {w} from {self}: {self.active_workers()} workers now")
        except KeyError:
            print(f"WARN: no worker with id {w.worker_id} among workers of {self}")
        self.worker_finished.emit(w.worker_id)


class WorkerJob:
    # The job is in scheduler queue but has not been passed to any thread yet
    STATUS_WAITING = "waiting"

    # The job has been passed (moveToThread) to a thread
    STATUS_DISPATCHED = "dispatched"

    # The job is executing on the thread
    STATUS_RUNNING = "running"

    # The job finished its execution
    STATUS_FINISHED = "finished"

    def __init__(self, worker: Worker, priority: int, status=STATUS_WAITING):
        self.worker = worker
        self.priority = priority
        self.status = status
        self.born = current_millis()

    # Returns True if schedule this job is better than scheduling the other job
    def __lt__(self, other):
        # Higher priority is better
        if self.priority > other.priority:
            return True
        if self.priority < other.priority:
            return False

        # Latest is better
        return self.born > other.born


class WorkerScheduler(QObject):
    PRIORITY_LOW = 10
    PRIORITY_BELOW_NORMAL = 20
    PRIORITY_NORMAL = 30
    PRIORITY_ABOVE_NORMAL = 40
    PRIORITY_HIGH = 50

    def __init__(self, max_num_threads: int):
        super().__init__()
        self.max_num_threads = max_num_threads
        self.threads: List[Thread] = []
        self.jobs = {}

        debug(f"Initializing WorkerScheduler with {self.max_num_threads} threads")

        for i in range(self.max_num_threads):
            t = Thread(tag=f"{i}")
            t.worker_started.connect(self._on_worker_started)
            t.worker_finished.connect(self._on_worker_finished)
            self.threads.append(t)

            # TODO: start only when required
            t.start()

    def schedule(self, worker: Worker, priority=PRIORITY_NORMAL):
        debug(f"Inserting Worker {worker.worker_id} into the scheduler queue with priority {priority}")

        # Push in the queue as waiting
        job = WorkerJob(worker, priority=priority, status=WorkerJob.STATUS_WAITING)
        self.jobs[worker.worker_id] = job
        self._dispatch_next_job_if_possible()

    def _on_worker_started(self, worker_id):
        # Change status
        job: WorkerJob = self.jobs.get(worker_id)
        job.status = WorkerJob.STATUS_RUNNING

    def _on_worker_finished(self, worker_id):
        # Remove job
        self.jobs.pop(worker_id)

        self._dispatch_next_job_if_possible()

    def _dispatch_next_job_if_possible(self):
        debug("Eventually dispatching next job")

        self._remove_canceled()

        # Dispatch a job to an available thread, if any

        # PRIORITY
        available_thread = self._get_first_available_thread()
        if not available_thread:
            debug("No available thread, not executing job by now")
            return
        # FIFO
        # available_thread = self._get_most_available_thread()

        debug(f"Available thread found: {available_thread}")

        # Get the job with the highest priority
        # TODO: smarter: priority queue with keys

        best_job_priority = None
        best_job = None

        for wid, job in self.jobs.items():
            if job.status != WorkerJob.STATUS_WAITING:
                continue
            if job.worker.can_execute() is True:
                if best_job_priority is None or job.priority > best_job_priority:
                    best_job = job
                    best_job_priority = job.priority

        if not best_job:
            debug("No job to dispatch")
            return

        debug(f"Scheduler selected the job to dispatch: Worker {best_job.worker.worker_id} with priority {best_job.priority}")

        best_job.status = WorkerJob.STATUS_DISPATCHED
        available_thread.enqueue_worker(best_job.worker)

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
        wid_zombies = []
        for wid, job in self.jobs.items():
            if job.worker.is_canceled():
                wid_zombies.append(wid)

        if wid_zombies:
            debug(f"Killing zombie workers: {wid_zombies}")
        for wid in wid_zombies:
            self.jobs.pop(wid)



def schedule(worker: Worker, priority=WorkerScheduler.PRIORITY_NORMAL):
    _worker_scheduler.schedule(worker, priority=priority)