from PyQt5.QtCore import QThread

debug_enabled = True

def debug(*args, **kwargs):
    if debug_enabled:
        print(f"[QThread {hex(int(QThread.currentThreadId()))}]", *args, **kwargs)