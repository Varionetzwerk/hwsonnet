"""Background worker threads for async hardware data collection."""

from __future__ import annotations

import time
from typing import Any, Callable

from PyQt6.QtCore import QThread, pyqtSignal

from src.utils.logger import logger


class StaticWorker(QThread):
    """Collects static (one-time) data in a background thread."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, collect_fn: Callable[[], Any], parent=None) -> None:
        super().__init__(parent)
        self._collect_fn = collect_fn

    def run(self) -> None:
        try:
            result = self._collect_fn()
            self.finished.emit(result)
        except Exception as exc:
            logger.error("StaticWorker error: %s", exc)
            self.error.emit(str(exc))


class DynamicWorker(QThread):
    """Periodically refreshes live hardware metrics."""

    data_ready = pyqtSignal(object)

    def __init__(
        self,
        data_obj: Any,
        update_fn: Callable[[Any], None],
        interval_ms: int = 1000,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._data = data_obj
        self._update_fn = update_fn
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        # Prime psutil percent counters (first call always returns 0)
        try:
            import psutil
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            pass

        while self._running:
            start = time.monotonic()
            try:
                self._update_fn(self._data)
                self.data_ready.emit(self._data)
            except Exception as exc:
                logger.debug("DynamicWorker update error: %s", exc)
            elapsed = time.monotonic() - start
            sleep_time = max(0.0, self._interval - elapsed)
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(3000)


class AllDataWorker(QThread):
    """Master worker that coordinates all collectors and emits a combined snapshot."""

    snapshot_ready = pyqtSignal(dict)

    def __init__(self, collectors: dict[str, Any], interval_ms: int = 1000, parent=None) -> None:
        super().__init__(parent)
        self._collectors = collectors   # name -> (info_obj, update_fn)
        self._interval = interval_ms / 1000.0
        self._running = True

    def run(self) -> None:
        # Prime CPU percent counters
        try:
            import psutil
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
            time.sleep(0.5)
        except Exception:
            pass

        while self._running:
            start = time.monotonic()
            snapshot: dict[str, Any] = {}
            for name, (data, fn) in self._collectors.items():
                try:
                    fn(data)
                    snapshot[name] = data
                except Exception as exc:
                    logger.debug("Collector '%s' error: %s", name, exc)
            self.snapshot_ready.emit(snapshot)
            elapsed = time.monotonic() - start
            sleep_time = max(0.0, self._interval - elapsed)
            if sleep_time > 0:
                self.msleep(int(sleep_time * 1000))

    def stop(self) -> None:
        self._running = False
        self.wait(4000)
