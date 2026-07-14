"""线程工具"""

from functools import wraps

from PySide6.QtCore import QThread

from ani2xcur.gui import logger


def run_on_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if QThread.currentThread() == QThread.mainThread():
            return func(*args, **kwargs)
        logger.warning("函数 %s 不在主线程调用", func.__name__)
        return func(*args, **kwargs)
    return wrapper


def is_main_thread() -> bool:
    return QThread.currentThread() == QThread.mainThread()


def ensure_main_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_main_thread():
            raise RuntimeError(f"函数 {func.__name__} 必须在主线程调用")
        return func(*args, **kwargs)
    return wrapper


def safe_signal_emit(signal, *args):
    try:
        signal.emit(*args)
    except Exception as e:
        logger.error("发射信号失败: %s", e)
