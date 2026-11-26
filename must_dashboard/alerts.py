from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

from .config import Settings


LOGGER = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AlertManager:
    """Opt-in Telegram alerting for grid outages, low battery, faults, and offline states."""

    def __init__(
        self,
        settings: Settings,
        sender: Callable[[str], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.settings = settings
        self._custom_sender = sender
        self._clock = clock or time.monotonic
        self._lock = threading.RLock()

        self._grid_down_streak = 0
        self._grid_up_streak = 0
        self._grid_is_down: bool | None = None
        self._grid_down_since_ts: float | None = None

        self._low_battery_active = False
        self._last_low_battery_alert_at = 0.0

        self._offline_alerted = False
        self._active_faults: set[str] = set()
        self._last_fault_alert_at = 0.0

        self._last_sent_at: str | None = None
        self._last_error: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.settings.telegram_bot_token and self.settings.telegram_chat_id)

    @property
    def active(self) -> bool:
        return bool(self.settings.telegram_enabled and (self.configured or self._custom_sender is not None))

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.settings.telegram_enabled,
                "configured": self.configured,
                "last_sent_at": self._last_sent_at,
                "last_error": self._last_error,
            }

    def evaluate_snapshot(self, snapshot: dict[str, Any]) -> None:
        if not snapshot:
            return
        now = self._clock()
        metrics = snapshot.get("metrics") or {}
        status = snapshot.get("status") or {}
        charger = status.get("charger") or {}
        inverter = status.get("inverter") or {}

        messages: list[str] = []

        # 1. Grid outage / restore (2-poll debounce)
        grid_v = metrics.get("grid_voltage_v")
        batt_v = metrics.get("battery_voltage_v")
        load_w = metrics.get("load_power_w")
        if grid_v is not None:
            if float(grid_v) < 50.0:
                self._grid_down_streak += 1
                self._grid_up_streak = 0
                if self._grid_is_down is None and self._grid_down_streak >= 2:
                    self._grid_is_down = True
                    self._grid_down_since_ts = now
                    messages.append(
                        f"⚡ Grid outage detected (0V). Battery: {batt_v}V, Load: {load_w}W."
                    )
                elif self._grid_is_down is False and self._grid_down_streak >= 2:
                    self._grid_is_down = True
                    self._grid_down_since_ts = now
                    messages.append(
                        f"⚡ Grid lost! Switched to battery ({batt_v}V, Load: {load_w}W)."
                    )
            else:
                self._grid_up_streak += 1
                self._grid_down_streak = 0
                if self._grid_is_down is None:
                    self._grid_is_down = False
                elif self._grid_is_down is True and self._grid_up_streak >= 2:
                    duration_min = (
                        max(1, int(round((now - self._grid_down_since_ts) / 60.0)))
                        if self._grid_down_since_ts is not None
                        else None
                    )
                    self._grid_is_down = False
                    self._grid_down_since_ts = None
                    dur_txt = f" after ~{duration_min} min" if duration_min is not None else ""
                    messages.append(
                        f"🔌 Grid restored{dur_txt} ({grid_v}V). Battery: {batt_v}V."
                    )

        # 2. Low battery alert with hysteresis and cooldown
        if batt_v is not None:
            threshold = self.settings.alert_low_battery_v
            if float(batt_v) <= threshold:
                if not self._low_battery_active and (
                    self._last_low_battery_alert_at == 0.0
                    or (now - self._last_low_battery_alert_at) >= self.settings.alert_cooldown_seconds
                ):
                    self._low_battery_active = True
                    self._last_low_battery_alert_at = now
                    messages.append(
                        f"🪫 Low battery warning: {batt_v}V (threshold {threshold}V, Load: {load_w}W)."
                    )
            elif float(batt_v) >= threshold + 0.4:
                self._low_battery_active = False

        # 3. Critical charger/inverter faults (ignoring informational PV-low at night)
        fault_codes = {
            f"charger:{flag['code']}"
            for flag in (charger.get("error_flags") or [])
            if flag.get("severity") == "error"
        } | {
            f"inverter:{flag['code']}"
            for flag in (inverter.get("error_flags") or [])
            if flag.get("severity") == "error"
        }
        new_faults = fault_codes - self._active_faults
        if new_faults and (
            self._last_fault_alert_at == 0.0
            or (now - self._last_fault_alert_at) >= self.settings.alert_cooldown_seconds
        ):
            self._last_fault_alert_at = now
            messages.append(f"🚨 Inverter fault(s): {', '.join(sorted(new_faults))}.")
        self._active_faults = fault_codes

        for text in messages:
            self._dispatch(text)

    def evaluate_health(self, health: dict[str, Any]) -> None:
        if not health:
            return
        status = health.get("status")
        failures = int(health.get("consecutive_failures") or 0)
        if status == "offline" and failures >= 3 and not self._offline_alerted:
            self._offline_alerted = True
            err = health.get("last_error") or "no response"
            self._dispatch(f"📡 MUST inverter telemetry offline ({failures} failures): {err}")
        elif status in {"online", "degraded"} and self._offline_alerted:
            self._offline_alerted = False
            self._dispatch("✅ MUST inverter telemetry connection recovered.")

    def _dispatch(self, text: str) -> None:
        if not self.active:
            return
        if self._custom_sender is not None:
            try:
                self._custom_sender(text)
                with self._lock:
                    self._last_sent_at = _utc_now()
                    self._last_error = None
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)
            return

        threading.Thread(
            target=self._send_telegram_http,
            args=(text,),
            name="must-telegram-alert",
            daemon=True,
        ).start()

    def _send_telegram_http(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.settings.telegram_chat_id,
                "text": f"MUST Power Desk\n{text}",
                "disable_web_page_preview": True,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if 200 <= response.status < 300:
                    with self._lock:
                        self._last_sent_at = _utc_now()
                        self._last_error = None
                else:
                    with self._lock:
                        self._last_error = f"Telegram HTTP {response.status}"
        except urllib.error.HTTPError as exc:
            with self._lock:
                self._last_error = f"Telegram HTTP {exc.code}"
            LOGGER.warning("Telegram alert delivery failed with HTTP %s", exc.code)
        except Exception as exc:
            # Never log URL containing bot token
            with self._lock:
                self._last_error = type(exc).__name__
            LOGGER.warning("Telegram alert delivery failed: %s", type(exc).__name__)
