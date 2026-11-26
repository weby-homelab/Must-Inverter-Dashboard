from __future__ import annotations

import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import Settings
from .decode import (
    CHARGER_SOURCE_PRIORITIES,
    ENERGY_USE_MODES,
    GRID_PROTECT_STANDARDS,
)
from .modbus import ModbusError
from .storage import Storage


class ControlError(RuntimeError):
    """Controlled validation, interlock, rate-limit, or execution error."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ParameterSpec:
    key: str
    tier: int
    address: int
    kind: str  # "enum" | "scaled" | "bit"
    section: str  # "charger_config" | "inverter_config"
    index: int
    scale: float = 1.0
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    enum_values: dict[int, str] | None = None
    bit_mask: int | None = None
    unit: str = ""

    def to_metadata(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "tier": self.tier,
            "address": self.address,
            "kind": self.kind,
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "enum": self.enum_values,
            "bit_mask": self.bit_mask,
            "unit": self.unit,
        }


PARAMETERS: dict[str, ParameterSpec] = {
    # Tier 1 — safe operational settings
    "energy_use_mode": ParameterSpec(
        key="energy_use_mode",
        tier=1,
        address=20109,
        kind="enum",
        section="inverter_config",
        index=8,
        enum_values=dict(ENERGY_USE_MODES),
    ),
    "charger_source_priority": ParameterSpec(
        key="charger_source_priority",
        tier=1,
        address=20143,
        kind="enum",
        section="inverter_config",
        index=42,
        enum_values=dict(CHARGER_SOURCE_PRIORITIES),
    ),
    "grid_protect_standard": ParameterSpec(
        key="grid_protect_standard",
        tier=1,
        address=20111,
        kind="enum",
        section="inverter_config",
        index=10,
        enum_values=dict(GRID_PROTECT_STANDARDS),
    ),
    "grid_max_charger_current_a": ParameterSpec(
        key="grid_max_charger_current_a",
        tier=1,
        address=20125,
        kind="scaled",
        section="inverter_config",
        index=24,
        scale=0.1,
        min_value=2.0,
        max_value=60.0,
        step=1.0,
        unit="A",
    ),
    "max_combine_charger_current_a": ParameterSpec(
        key="max_combine_charger_current_a",
        tier=1,
        address=20132,
        kind="scaled",
        section="inverter_config",
        index=31,
        scale=0.1,
        min_value=10.0,
        max_value=60.0,
        step=1.0,
        unit="A",
    ),
    "system_overload_restart_forbid": ParameterSpec(
        key="system_overload_restart_forbid",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0001,
    ),
    "system_overtemp_restart_forbid": ParameterSpec(
        key="system_overtemp_restart_forbid",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0002,
    ),
    "system_overload_bypass_forbid": ParameterSpec(
        key="system_overload_bypass_forbid",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0004,
    ),
    "system_auto_turn_page_forbid": ParameterSpec(
        key="system_auto_turn_page_forbid",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0008,
    ),
    "system_grid_buzz_enable": ParameterSpec(
        key="system_grid_buzz_enable",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0010,
    ),
    "system_buzz_forbid": ParameterSpec(
        key="system_buzz_forbid",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0020,
    ),
    "system_lcd_light_enable": ParameterSpec(
        key="system_lcd_light_enable",
        tier=1,
        address=20142,
        kind="bit",
        section="inverter_config",
        index=41,
        bit_mask=0x0040,
    ),
    # Tier 2 — 24V battery voltage thresholds (extra confirmation & invariant checks)
    "battery_low_voltage_v": ParameterSpec(
        key="battery_low_voltage_v",
        tier=2,
        address=20127,
        kind="scaled",
        section="inverter_config",
        index=26,
        scale=0.1,
        min_value=20.0,
        max_value=26.0,
        step=0.1,
        unit="V",
    ),
    "normal_voltage_point_v": ParameterSpec(
        key="normal_voltage_point_v",
        tier=2,
        address=20118,
        kind="scaled",
        section="inverter_config",
        index=17,
        scale=0.1,
        min_value=21.0,
        max_value=27.0,
        step=0.1,
        unit="V",
    ),
    "start_sell_voltage_point_v": ParameterSpec(
        key="start_sell_voltage_point_v",
        tier=2,
        address=20119,
        kind="scaled",
        section="inverter_config",
        index=18,
        scale=0.1,
        min_value=24.0,
        max_value=29.0,
        step=0.1,
        unit="V",
    ),
    "float_voltage_v": ParameterSpec(
        key="float_voltage_v",
        tier=2,
        address=10103,
        kind="scaled",
        section="charger_config",
        index=2,
        scale=0.1,
        min_value=25.0,
        max_value=29.5,
        step=0.1,
        unit="V",
    ),
    "absorption_voltage_v": ParameterSpec(
        key="absorption_voltage_v",
        tier=2,
        address=10104,
        kind="scaled",
        section="charger_config",
        index=3,
        scale=0.1,
        min_value=25.5,
        max_value=30.0,
        step=0.1,
        unit="V",
    ),
}


PRESETS: dict[str, dict[str, Any]] = {
    "fast_charge": {
        "changes": {
            "charger_source_priority": 2,
            "grid_max_charger_current_a": 30.0,
            "max_combine_charger_current_a": 60.0,
        },
    },
    "gentle_charge": {
        "changes": {
            "charger_source_priority": 2,
            "grid_max_charger_current_a": 15.0,
            "max_combine_charger_current_a": 40.0,
        },
    },
    "ups_utility": {
        "changes": {
            "energy_use_mode": 3,
            "grid_protect_standard": 1,
            "charger_source_priority": 2,
        },
    },
    "solar_first": {
        "changes": {
            "energy_use_mode": 1,
            "charger_source_priority": 0,
        },
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _extract_current_raw(spec: ParameterSpec, raw_sections: dict[str, list[int]]) -> int | None:
    registers = raw_sections.get(spec.section)
    if not registers or spec.index >= len(registers):
        return None
    return int(registers[spec.index]) & 0xFFFF


def _decode_raw(spec: ParameterSpec, raw_value: int) -> Any:
    if spec.kind == "enum":
        return int(raw_value)
    if spec.kind == "scaled":
        return round(int(raw_value) * spec.scale, 3)
    if spec.kind == "bit":
        return bool(int(raw_value) & int(spec.bit_mask or 0))
    raise ControlError(f"unsupported parameter kind: {spec.kind}", 500)


def _encode_value(spec: ParameterSpec, value: Any, current_word: int) -> tuple[Any, int]:
    if spec.kind == "enum":
        if isinstance(value, bool):
            raise ControlError(f"invalid enum value for {spec.key}", 400)
        try:
            int_val = int(value)
        except (TypeError, ValueError):
            raise ControlError(f"invalid enum value for {spec.key}", 400) from None
        if not spec.enum_values or int_val not in spec.enum_values:
            raise ControlError(f"unsupported value {int_val} for {spec.key}", 400)
        return int_val, int_val

    if spec.kind == "scaled":
        if isinstance(value, bool):
            raise ControlError(f"invalid numeric value for {spec.key}", 400)
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ControlError(f"invalid numeric value for {spec.key}", 400) from None
        if spec.min_value is not None and num < spec.min_value - 1e-9:
            raise ControlError(f"{spec.key} must be >= {spec.min_value} {spec.unit}".strip(), 400)
        if spec.max_value is not None and num > spec.max_value + 1e-9:
            raise ControlError(f"{spec.key} must be <= {spec.max_value} {spec.unit}".strip(), 400)
        raw_int = int(round(num / spec.scale))
        normalized = round(raw_int * spec.scale, 3)
        return normalized, raw_int

    if spec.kind == "bit":
        if not isinstance(value, bool):
            raise ControlError(f"{spec.key} requires a boolean value", 400)
        mask = int(spec.bit_mask or 0)
        new_word = (current_word | mask) if value else (current_word & ~mask)
        return value, new_word & 0xFFFF

    raise ControlError(f"unsupported parameter kind: {spec.kind}", 500)


class ControlManager:
    """Safe, allowlisted, rate-limited control plane for MUST PV1800 configuration."""

    def __init__(self, settings: Settings, poller: Any, storage: Storage) -> None:
        self.settings = settings
        self.poller = poller
        self.storage = storage
        self._lock = threading.RLock()
        self._unlock_token: str | None = None
        self._unlock_expires_at: float = 0.0
        self._last_write_monotonic: float = 0.0
        self._write_timestamps: deque[float] = deque()

    def _prune_budget(self, now: float) -> None:
        cutoff = now - 3600.0
        while self._write_timestamps and self._write_timestamps[0] < cutoff:
            self._write_timestamps.popleft()

    def _is_unlocked_locked(self, now: float) -> bool:
        if not self.settings.enable_write:
            return False
        if not self._unlock_token or now >= self._unlock_expires_at:
            self._unlock_token = None
            self._unlock_expires_at = 0.0
            return False
        return True

    def _interlock_reason(self) -> tuple[str | None, dict[str, Any] | None, dict[str, Any]]:
        health = self.poller.health() or {}
        latest = self.poller.latest()
        if not self.settings.enable_write:
            return "write_disabled", latest, health
        if health.get("status") in {"offline", "stale", "starting"} or latest is None:
            return "telemetry_unavailable", latest, health
        raw = latest.get("raw") or {}
        if not raw.get("charger_config") or not raw.get("inverter_config"):
            return "config_unavailable", latest, health
        return None, latest, health

    def status(self) -> dict[str, Any]:
        with self._lock:
            now = time.monotonic()
            self._prune_budget(now)
            unlocked = self._is_unlocked_locked(now)
            expires_in = max(0, int(round(self._unlock_expires_at - now))) if unlocked else 0
            cooldown_rem = 0.0
            if self._last_write_monotonic > 0:
                cooldown_rem = max(0.0, self.settings.write_cooldown - (now - self._last_write_monotonic))
            writes_last_hour = len(self._write_timestamps)
            interlock_reason, _latest, _health = self._interlock_reason()

        return {
            "write_enabled": self.settings.enable_write,
            "unlocked": unlocked,
            "expires_in_seconds": expires_in,
            "unlock_ttl_seconds": self.settings.write_unlock_ttl,
            "cooldown_seconds": self.settings.write_cooldown,
            "cooldown_remaining_seconds": round(cooldown_rem, 1),
            "writes_last_hour": writes_last_hour,
            "max_writes_per_hour": self.settings.max_writes_per_hour,
            "interlock_reason": interlock_reason,
            "parameters": {key: spec.to_metadata() for key, spec in PARAMETERS.items()},
            "presets": {key: dict(val["changes"]) for key, val in PRESETS.items()},
        }

    def unlock(self) -> dict[str, Any]:
        if not self.settings.enable_write:
            raise ControlError("Inverter writes are disabled on the server (MUST_ENABLE_WRITE=false)", 403)
        interlock_reason, _latest, _health = self._interlock_reason()
        if interlock_reason == "telemetry_unavailable":
            raise ControlError("Cannot unlock while inverter telemetry is offline or stale", 409)
        if interlock_reason == "config_unavailable":
            raise ControlError("Cannot unlock until configuration registers are read", 409)

        with self._lock:
            token = secrets.token_urlsafe(24)
            self._unlock_token = token
            self._unlock_expires_at = time.monotonic() + self.settings.write_unlock_ttl

        return {
            "token": token,
            "expires_in_seconds": self.settings.write_unlock_ttl,
            "status": self.status(),
        }

    def lock(self) -> dict[str, Any]:
        with self._lock:
            self._unlock_token = None
            self._unlock_expires_at = 0.0
        return {"status": self.status()}

    def preview(self, changes: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(changes, dict) or not changes:
            raise ControlError("changes must be a non-empty object", 400)

        latest = self.poller.latest()
        if not latest or not (latest.get("raw") or {}).get("inverter_config") or not (latest.get("raw") or {}).get("charger_config"):
            raise ControlError("Inverter configuration is not yet available", 409)

        raw_sections: dict[str, list[int]] = latest["raw"]
        config = latest.get("configuration") or {}
        inv_cfg = config.get("inverter") or {}
        chg_cfg = config.get("charger") or {}
        inv_status = (latest.get("status") or {}).get("inverter") or {}

        unknown = [key for key in changes if key not in PARAMETERS]
        if unknown:
            raise ControlError(f"Parameter(s) not allowlisted for write: {', '.join(unknown)}", 400)

        # Group raw words by register address so multiple bit updates on 20142 merge cleanly.
        word_state: dict[int, int] = {}
        items: list[dict[str, Any]] = []
        proposed_decoded: dict[str, Any] = {}

        for key, target_input in changes.items():
            spec = PARAMETERS[key]
            base_raw = _extract_current_raw(spec, raw_sections)
            if base_raw is None:
                raise ControlError(f"Register {spec.address} unavailable in current snapshot", 409)
            current_word = word_state.get(spec.address, base_raw)
            current_decoded = _decode_raw(spec, base_raw)
            normalized_target, new_word = _encode_value(spec, target_input, current_word)
            word_state[spec.address] = new_word
            proposed_decoded[key] = normalized_target
            is_noop = (current_decoded == normalized_target) if spec.kind == "bit" else (base_raw == new_word)
            items.append({
                "param_key": key,
                "tier": spec.tier,
                "address": spec.address,
                "kind": spec.kind,
                "unit": spec.unit,
                "current_value": current_decoded,
                "target_value": normalized_target,
                "current_raw": base_raw,
                "target_raw": new_word,
                "is_noop": is_noop,
            })

        # Cross-field safety validations
        effective_grid_cur = proposed_decoded.get(
            "grid_max_charger_current_a", inv_cfg.get("grid_max_charger_current_a")
        )
        effective_combine_cur = proposed_decoded.get(
            "max_combine_charger_current_a", inv_cfg.get("max_combine_charger_current_a")
        )
        if effective_grid_cur is not None and effective_combine_cur is not None:
            if float(effective_grid_cur) > float(effective_combine_cur) + 1e-6:
                raise ControlError(
                    f"grid_max_charger_current_a ({effective_grid_cur} A) cannot exceed "
                    f"max_combine_charger_current_a ({effective_combine_cur} A)",
                    400,
                )

        has_tier2 = any(item["tier"] == 2 and not item["is_noop"] for item in items)
        if any(item["tier"] == 2 for item in items):
            grade = inv_status.get("battery_voltage_grade_code")
            if grade is not None and int(grade) != 24:
                raise ControlError(f"Tier 2 battery thresholds are locked to 24V systems (detected {grade}V)", 409)

            low_v = float(proposed_decoded.get("battery_low_voltage_v", inv_cfg.get("battery_low_voltage_v") or 24.0))
            norm_v = float(proposed_decoded.get("normal_voltage_point_v", inv_cfg.get("normal_voltage_point_v") or 24.4))
            sell_v = float(proposed_decoded.get("start_sell_voltage_point_v", inv_cfg.get("start_sell_voltage_point_v") or 26.8))
            flt_v = float(proposed_decoded.get("float_voltage_v", chg_cfg.get("float_voltage_v") or 27.0))
            abs_v = float(proposed_decoded.get("absorption_voltage_v", chg_cfg.get("absorption_voltage_v") or 28.8))
            high_v = float(inv_cfg.get("battery_high_voltage_v") or chg_cfg.get("battery_high_voltage_v") or 30.0)

            if not (low_v < norm_v < sell_v <= flt_v <= abs_v <= high_v):
                raise ControlError(
                    "Invalid 24V threshold ordering: require "
                    f"cutoff ({low_v}V) < back_to_grid ({norm_v}V) < back_to_batt ({sell_v}V) "
                    f"<= float ({flt_v}V) <= bulk ({abs_v}V) <= high_limit ({high_v}V)",
                    400,
                )

        # Ensure final combined target_raw for shared register (20142) is attached to each item
        for item in items:
            item["target_raw"] = word_state[item["address"]]

        has_changes = any(not item["is_noop"] for item in items)
        warnings: list[str] = []
        if has_tier2:
            warnings.append("tier2_battery_thresholds")
        if any(item["param_key"] == "energy_use_mode" and not item["is_noop"] for item in items):
            warnings.append("output_mode_switch")

        return {
            "items": items,
            "has_changes": has_changes,
            "requires_tier2_confirm": has_tier2,
            "warnings": warnings,
        }

    def apply(
        self,
        changes: dict[str, Any],
        *,
        token: str,
        client_ip: str,
        reason: str = "manual",
        confirm_tier2: bool = False,
    ) -> dict[str, Any]:
        if not self.settings.enable_write:
            raise ControlError("Inverter writes are disabled on the server (MUST_ENABLE_WRITE=false)", 403)

        interlock_reason, _latest, _health = self._interlock_reason()
        if interlock_reason is not None:
            raise ControlError(f"Write blocked by safety interlock: {interlock_reason}", 409)

        with self._lock:
            now = time.monotonic()
            if not self._is_unlocked_locked(now) or not token or not secrets.compare_digest(token, self._unlock_token or ""):
                raise ControlError("Control session is locked or expired; unlock before writing", 403)

            preview_data = self.preview(changes)
            if preview_data["requires_tier2_confirm"] and not confirm_tier2:
                raise ControlError("Tier 2 battery threshold changes require explicit confirmation", 400)

            items = preview_data["items"]
            active_items = [item for item in items if not item["is_noop"]]
            if active_items:
                self._prune_budget(now)
                if self._last_write_monotonic > 0:
                    elapsed = now - self._last_write_monotonic
                    if elapsed < self.settings.write_cooldown:
                        raise ControlError(
                            f"Write cooldown active ({self.settings.write_cooldown - elapsed:.1f}s remaining)",
                            429,
                        )
                if len(self._write_timestamps) >= self.settings.max_writes_per_hour:
                    raise ControlError(
                        f"Hourly write limit reached ({self.settings.max_writes_per_hour}/h)",
                        429,
                    )

            # Group non-noop items by register address so bitmask updates perform 1 EEPROM write.
            results: list[dict[str, Any]] = []
            noop_items = [item for item in items if item["is_noop"]]
            for item in noop_items:
                audit_id = self.storage.insert_audit(
                    created_at=_utc_now(),
                    client_ip=client_ip,
                    param_key=item["param_key"],
                    tier=item["tier"],
                    register_address=item["address"],
                    old_raw=item["current_raw"],
                    new_raw=item["target_raw"],
                    verified_raw=item["current_raw"],
                    old_value=item["current_value"],
                    new_value=item["target_value"],
                    status="noop",
                    reason=reason,
                )
                results.append({**item, "status": "noop", "written": False, "audit_id": audit_id})

            grouped: dict[int, list[dict[str, Any]]] = {}
            for item in active_items:
                grouped.setdefault(item["address"], []).append(item)

            any_written = False
            for address, group_items in grouped.items():
                target_raw = group_items[-1]["target_raw"]
                old_raw = group_items[0]["current_raw"]
                try:
                    write_res = self.poller.write_register(address, target_raw, verify=True)
                    write_status = write_res["status"]
                    verified_raw = write_res.get("after")
                    if write_res.get("written"):
                        any_written = True
                        write_now = time.monotonic()
                        self._last_write_monotonic = write_now
                        self._write_timestamps.append(write_now)
                    for item in group_items:
                        audit_id = self.storage.insert_audit(
                            created_at=_utc_now(),
                            client_ip=client_ip,
                            param_key=item["param_key"],
                            tier=item["tier"],
                            register_address=address,
                            old_raw=write_res.get("before", old_raw),
                            new_raw=target_raw,
                            verified_raw=verified_raw,
                            old_value=item["current_value"],
                            new_value=item["target_value"],
                            status=write_status,
                            reason=reason,
                        )
                        results.append({
                            **item,
                            "status": write_status,
                            "written": bool(write_res.get("written")),
                            "verified_raw": verified_raw,
                            "audit_id": audit_id,
                        })
                except (ModbusError, ValueError, OSError) as exc:
                    for item in group_items:
                        self.storage.insert_audit(
                            created_at=_utc_now(),
                            client_ip=client_ip,
                            param_key=item["param_key"],
                            tier=item["tier"],
                            register_address=address,
                            old_raw=old_raw,
                            new_raw=target_raw,
                            verified_raw=None,
                            old_value=item["current_value"],
                            new_value=item["target_value"],
                            status="error",
                            reason=reason,
                            error_message=str(exc),
                        )
                    raise ControlError(f"Modbus write failed for register {address}: {exc}", 502) from exc

        updated_snapshot = None
        if any_written:
            try:
                updated_snapshot = self.poller.refresh_now(include_config=True)
            except Exception:
                updated_snapshot = self.poller.latest()

        return {
            "results": results,
            "written_count": sum(1 for item in results if item.get("written")),
            "snapshot": updated_snapshot or self.poller.latest(),
            "status": self.status(),
        }

    def apply_preset(
        self,
        preset_name: str,
        *,
        token: str,
        client_ip: str,
        confirm_tier2: bool = False,
    ) -> dict[str, Any]:
        if preset_name not in PRESETS:
            raise ControlError(f"Unknown preset: {preset_name}", 400)
        return self.apply(
            dict(PRESETS[preset_name]["changes"]),
            token=token,
            client_ip=client_ip,
            reason=f"preset:{preset_name}",
            confirm_tier2=confirm_tier2,
        )

    def rollback(
        self,
        audit_id: int,
        *,
        token: str,
        client_ip: str,
        confirm_tier2: bool = False,
    ) -> dict[str, Any]:
        entry = self.storage.get_audit(audit_id)
        if not entry:
            raise ControlError(f"Audit entry {audit_id} not found", 404)
        param_key = entry["param_key"]
        if param_key not in PARAMETERS:
            raise ControlError(f"Parameter {param_key} is not allowlisted", 400)
        if entry["old_raw"] is None:
            raise ControlError("Audit entry has no previous value to restore", 400)

        spec = PARAMETERS[param_key]
        target_value = entry["old_value"] if entry["old_value"] is not None else _decode_raw(spec, int(entry["old_raw"]))
        return self.apply(
            {param_key: target_value},
            token=token,
            client_ip=client_ip,
            reason=f"rollback:{audit_id}",
            confirm_tier2=confirm_tier2,
        )
