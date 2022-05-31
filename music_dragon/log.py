from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication

from music_dragon.utils import current_execution_millis

debug_enabled = False

_main_thread_id = None
_threads_strings = {}


def debug(*args, **kwargs):

    global _main_thread_id
    if debug_enabled:
        if _main_thread_id is None:
            _main_thread_id = hex(int(QApplication.instance().thread().currentThreadId()))

        thread_id = hex(int(QThread.currentThreadId()))
        if thread_id in _threads_strings:
            thread_str = _threads_strings[thread_id]
        else:
            thread_str = f"background {len(_threads_strings)}"
            _threads_strings[thread_id] = thread_str

        print(f"[{current_execution_millis()}] "
              f"{{{'main' if thread_id == _main_thread_id else thread_str}}}",
              *args, **kwargs)

