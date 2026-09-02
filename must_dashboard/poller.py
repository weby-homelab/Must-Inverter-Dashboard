from __future__ import annotations

import copy
import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .config import Settings
from .modbus import ModbusError, ModbusRTU
from .storage import Storage


LOGGER = logging.getLogger(__name__)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class EventHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: set[queue.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> queue.Queue[dict[str, Any]]:
        subscriber: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=8)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[dict[str, Any]]) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)

    def publish(self, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = tuple(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(event)
            except queue.Full:
                try:
                    subscriber.get_nowait()
                    subscriber.put_nowait(event)
                except queue.Empty:
                    pass


class InverterPoller:
    def __init__(self, settings: Settings, storage: Storage, events: EventHub) -> None:
        self.settings = settings
        self.storage = storage
        self.events = events
        self.client = ModbusRTU(settings)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._latest = storage.latest_payload()
        self._last_stored_ts = storage.last_sample_ts()
        self._last_config_at = 0.0
        self._last_prune_at = 0.0
        self._health: dict[str, Any] = {
            "version": __version__,
            "status": "starting",
            "last_attempt_at": None,
            "last_success_at": self._latest.get("captured_at") if self._latest else None,
            "last_error": None,
            "consecutive_failures": 0,
            "successful_polls": 0,
            "failed_polls": 0,
            "latency_ms": None,
        }

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="must-inverter-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.client.close()
        if self._thread is not None:
            self._thread.join(timeout=max(2.0, self.settings.serial_timeout + 1.0))

    def latest(self) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self._latest)

    def health(self) -> dict[str, Any]:
        with self._lock:
            health = copy.deepcopy(self._health)
            latest = self._latest
        if latest:
            try:
                captured_ts = datetime.fromisoformat(latest["captured_at"].replace("Z", "+00:00")).timestamp()
                health["sample_age_seconds"] = max(0, round(time.time() - captured_ts, 1))
                if health["status"] == "online" and health["sample_age_seconds"] > max(60, self.settings.poll_interval * 3):
                    health["status"] = "stale"
            except (KeyError, TypeError, ValueError):
                health["sample_age_seconds"] = None
        else:
            health["sample_age_seconds"] = None
        health["storage"] = self.storage.stats()
        return health

    def _run(self) -> None:
        LOGGER.info(
            "starting poller on %s at %s baud, slave %s",
            self.settings.serial_port,
            self.settings.baudrate,
            self.settings.slave_id,
        )
        while not self._stop.is_set():
            started = time.monotonic()
            attempt_at = utc_now()
            with self._lock:
                self._health["last_attempt_at"] = attempt_at
            try:
                include_config = time.monotonic() - self._last_config_at >= self.settings.config_interval
                snapshot = self.client.poll_once(include_config=include_config)
                config_errors = set(snapshot.get("connection", {}).get("section_errors", {})) & {
                    "charger_config",
                    "inverter_config",
                }
                if include_config and snapshot.get("configuration") is not None and not config_errors:
                    self._last_config_at = time.monotonic()

                captured_ts = int(
                    datetime.fromisoformat(snapshot["captured_at"].replace("Z", "+00:00")).timestamp()
                )
                if self._last_stored_ts is None or captured_ts - self._last_stored_ts >= self.settings.sample_interval:
                    self.storage.insert_sample(snapshot)
                    self._last_stored_ts = captured_ts

                if time.monotonic() - self._last_prune_at >= 21600:
                    deleted = self.storage.prune(self.settings.retention_days)
                    self._last_prune_at = time.monotonic()
                    if deleted:
                        LOGGER.info("pruned %s samples", deleted)

                with self._lock:
                    self._latest = snapshot
                    section_errors = snapshot.get("connection", {}).get("section_errors", {})
                    degraded_error = "; ".join(f"{key}: {value}" for key, value in section_errors.items())
                    self._health.update(
                        {
                            "status": snapshot.get("connection", {}).get("status", "online"),
                            "last_success_at": snapshot["captured_at"],
                            "last_error": degraded_error or None,
                            "consecutive_failures": 0,
                            "successful_polls": self._health["successful_polls"] + 1,
                            "latency_ms": snapshot.get("connection", {}).get("latency_ms"),
                        }
                    )
                self.events.publish({"type": "snapshot", "data": snapshot, "health": self.health()})
            except Exception as exc:
                self.client.close()
                with self._lock:
                    self._health.update(
                        {
                            "status": "offline",
                            "last_error": str(exc),
                            "consecutive_failures": self._health["consecutive_failures"] + 1,
                            "failed_polls": self._health["failed_polls"] + 1,
                        }
                    )
                LOGGER.error("poll cycle failed: %s", exc)
                self.events.publish({"type": "health", "health": self.health()})

            elapsed = time.monotonic() - started
            self._stop.wait(max(0.0, self.settings.poll_interval - elapsed))
