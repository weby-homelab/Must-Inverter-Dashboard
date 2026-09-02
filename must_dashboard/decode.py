from __future__ import annotations

from typing import Any


def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def value(registers: list[int] | None, index: int, *, signed: bool = True) -> int | None:
    if registers is None or index >= len(registers):
        return None
    return signed16(registers[index]) if signed else registers[index]


def scaled(registers: list[int] | None, index: int, factor: float) -> float | None:
    raw = value(registers, index)
    return None if raw is None else round(raw * factor, 3)


def version(registers: list[int] | None, index: int) -> str | None:
    raw = value(registers, index)
    if raw is None:
        return None
    if raw == 0:
        return "1.00.00"
    return f"{raw // 10000}.{(raw // 100) % 100:02}.{raw % 100:02}"


def _model(registers: list[int] | None) -> str | None:
    machine_type = value(registers, 0)
    software_raw = value(registers, 4)
    if machine_type == 1600:
        return "PC1600"
    if machine_type == 1800:
        return "PV1800" if (software_raw or 0) > 20000 else "PH1800"
    if machine_type == 3000:
        return "PH3000"
    if machine_type == 3500:
        return "PV3500"
    return f"MUST ({machine_type})" if machine_type is not None else None


def decode_identity(registers: list[int] | None) -> dict[str, Any] | None:
    if not registers:
        return None
    serial_number = None
    if len(registers) > 2:
        serial_number = f"{registers[1]:04X}{registers[2]:04X}"
    return {
        "model": _model(registers),
        "machine_type_code": value(registers, 0),
        "serial_number": serial_number,
        "hardware_version": version(registers, 3),
        "software_version": version(registers, 4),
        "battery_voltage_raw": value(registers, 8),
        "inverter_voltage_raw": value(registers, 9),
        "grid_voltage_raw": value(registers, 10),
        "bus_voltage_raw": value(registers, 11),
        "control_current_raw": value(registers, 12),
        "inverter_current_raw": value(registers, 13),
        "grid_current_raw": value(registers, 14),
        "load_current_raw": value(registers, 15),
    }


def decode_charger_status(registers: list[int] | None) -> dict[str, Any] | None:
    if not registers:
        return None
    return {
        "work_state_code": value(registers, 0),
        "mppt_state_code": value(registers, 1),
        "charging_state_code": value(registers, 2),
        "pv_voltage_v": scaled(registers, 4, 0.1),
        "battery_voltage_v": scaled(registers, 5, 0.1),
        "charger_current_a": scaled(registers, 6, 0.1),
        "charger_power_w": value(registers, 7),
        "radiator_temperature_c": value(registers, 8),
        "external_temperature_c": value(registers, 9),
        "battery_relay_code": value(registers, 10),
        "pv_relay_code": value(registers, 11),
        "error_code": value(registers, 12),
        "warning_code": value(registers, 13),
        "battery_voltage_grade_code": value(registers, 14),
        "rated_current_a": scaled(registers, 15, 0.1),
        "accumulated_power_wh": _u32_tenths(registers, 16),
        "accumulated_time": _time_value(registers, 18),
    }


def decode_inverter_status(registers: list[int] | None) -> dict[str, Any] | None:
    if not registers:
        return None
    return {
        "work_state_code": value(registers, 0),
        "ac_voltage_grade_code": value(registers, 1),
        "rated_power_w": value(registers, 2),
        "battery_voltage_v": scaled(registers, 4, 0.1),
        "inverter_voltage_v": scaled(registers, 5, 0.1),
        "grid_voltage_v": scaled(registers, 6, 0.1),
        "bus_voltage_v": scaled(registers, 7, 0.1),
        "control_current_a": scaled(registers, 8, 0.1),
        "inverter_current_a": scaled(registers, 9, 0.1),
        "grid_current_a": scaled(registers, 10, 0.1),
        "load_current_a": scaled(registers, 11, 0.1),
        "inverter_power_w": value(registers, 12),
        "grid_power_w": value(registers, 13),
        "load_power_w": value(registers, 14),
        "load_percent": value(registers, 15),
        "inverter_apparent_power_va": value(registers, 16),
        "grid_apparent_power_va": value(registers, 17),
        "load_apparent_power_va": value(registers, 18),
        "inverter_reactive_power_var": value(registers, 20),
        "grid_reactive_power_var": value(registers, 21),
        "load_reactive_power_var": value(registers, 22),
        "inverter_frequency_hz": scaled(registers, 24, 0.01),
        "grid_frequency_hz": scaled(registers, 25, 0.01),
        "inverter_max_number": value(registers, 28),
        "combine_type_code": value(registers, 29),
        "inverter_number": value(registers, 30),
        "ac_radiator_temperature_c": value(registers, 32),
        "transformer_temperature_c": value(registers, 33),
        "dc_radiator_temperature_c": value(registers, 34),
        "inverter_relay_code": value(registers, 36),
        "grid_relay_code": value(registers, 37),
        "load_relay_code": value(registers, 38),
        "n_line_relay_code": value(registers, 39),
        "dc_relay_code": value(registers, 40),
        "earth_relay_code": value(registers, 41),
        "accumulated_charger_power_wh": _u32_tenths(registers, 44),
        "accumulated_discharger_power_wh": _u32_tenths(registers, 46),
        "accumulated_buy_power_wh": _u32_tenths(registers, 48),
        "accumulated_sell_power_wh": _u32_tenths(registers, 50),
        "accumulated_load_power_wh": _u32_tenths(registers, 52),
        "accumulated_self_use_power_wh": _u32_tenths(registers, 54),
        "accumulated_pv_sell_power_wh": _u32_tenths(registers, 56),
        "accumulated_grid_charger_power_wh": _u32_tenths(registers, 58),
        "serial_number": _register_pair_hex(registers, 68),
        "hardware_version": version(registers, 70),
        "software_version": version(registers, 71),
        "battery_power_w": value(registers, 72),
        "battery_current_raw": value(registers, 73),
        "battery_voltage_grade_code": value(registers, 74),
        "rated_power_w_from_status": value(registers, 76),
        "communication_protocol_version": version(registers, 77),
        "arrow_flag": value(registers, 78),
    }


def decode_charger_config(registers: list[int] | None) -> dict[str, Any] | None:
    if not registers:
        return None
    return {
        "charger_work_enabled": bool(value(registers, 0)),
        "absorb_voltage_v": scaled(registers, 1, 0.1),
        "float_voltage_v": scaled(registers, 2, 0.1),
        "absorption_voltage_v": scaled(registers, 3, 0.1),
        "battery_low_voltage_v": scaled(registers, 4, 0.1),
        "battery_high_voltage_v": scaled(registers, 6, 0.1),
        "max_charger_current_a": scaled(registers, 7, 0.1),
        "absorb_charger_current_a": scaled(registers, 8, 0.1),
        "battery_type_code": value(registers, 9),
        "battery_capacity_ah": value(registers, 10),
        "remove_accumulated_data_code": value(registers, 11),
        "equalization_enabled": bool(value(registers, 17)),
        "equalization_voltage_v": scaled(registers, 18, 0.1),
        "equalization_time_min": value(registers, 20),
        "equalization_timeout_min": value(registers, 21),
        "equalization_interval_days": value(registers, 22),
        "equalization_immediate_code": value(registers, 23),
    }


def decode_inverter_config(registers: list[int] | None) -> dict[str, Any] | None:
    if not registers:
        return None
    return {
        "offgrid_work_enabled": bool(value(registers, 0)),
        "output_voltage_v": scaled(registers, 1, 0.1),
        "output_frequency_hz": scaled(registers, 2, 0.01),
        "search_mode_enabled": bool(value(registers, 3)),
        "discharge_to_grid_enabled": bool(value(registers, 7)),
        "energy_use_mode_code": value(registers, 8),
        "grid_protect_standard_code": value(registers, 10),
        "solar_use_aim_code": value(registers, 11),
        "max_discharger_current_a": scaled(registers, 12, 0.1),
        "normal_voltage_point_v": scaled(registers, 17, 0.1),
        "start_sell_voltage_point_v": scaled(registers, 18, 0.1),
        "grid_max_charger_current_a": scaled(registers, 24, 0.1),
        "battery_low_voltage_v": scaled(registers, 26, 0.1),
        "battery_high_voltage_v": scaled(registers, 27, 0.1),
        "max_combine_charger_current_a": scaled(registers, 31, 0.1),
        "system_setting_code": value(registers, 41),
        "charger_source_priority_code": value(registers, 42),
        "solar_power_balance_code": value(registers, 43),
        "raw_register_count": len(registers),
    }


def decode_snapshot(
    *,
    sections: dict[str, list[int]],
    captured_at: str,
    source: dict[str, Any],
    errors: dict[str, str],
    latency_ms: float,
) -> dict[str, Any]:
    identity = decode_identity(sections.get("identity"))
    charger = decode_charger_status(sections.get("charger_status"))
    inverter = decode_inverter_status(sections.get("inverter_status"))
    charger_config = decode_charger_config(sections.get("charger_config"))
    inverter_config = decode_inverter_config(sections.get("inverter_config"))

    def first(*values: Any) -> Any:
        return next((item for item in values if item is not None), None)

    metrics = {
        "battery_voltage_v": first(
            inverter and inverter.get("battery_voltage_v"),
            charger and charger.get("battery_voltage_v"),
        ),
        "pv_voltage_v": charger and charger.get("pv_voltage_v"),
        "pv_current_a": charger and charger.get("charger_current_a"),
        "pv_power_w": charger and charger.get("charger_power_w"),
        "inverter_voltage_v": first(
            inverter and inverter.get("inverter_voltage_v"),
            identity and _raw_tenths(identity.get("inverter_voltage_raw")),
        ),
        "grid_voltage_v": first(
            inverter and inverter.get("grid_voltage_v"),
            identity and _raw_tenths(identity.get("grid_voltage_raw")),
        ),
        "bus_voltage_v": inverter and inverter.get("bus_voltage_v"),
        "inverter_current_a": inverter and inverter.get("inverter_current_a"),
        "grid_current_a": inverter and inverter.get("grid_current_a"),
        "load_current_a": inverter and inverter.get("load_current_a"),
        "inverter_power_w": inverter and inverter.get("inverter_power_w"),
        "grid_power_w": inverter and inverter.get("grid_power_w"),
        "load_power_w": inverter and inverter.get("load_power_w"),
        "load_percent": inverter and inverter.get("load_percent"),
        "inverter_frequency_hz": inverter and inverter.get("inverter_frequency_hz"),
        "grid_frequency_hz": inverter and inverter.get("grid_frequency_hz"),
        "battery_power_w": inverter and inverter.get("battery_power_w"),
        "ac_radiator_temperature_c": inverter and inverter.get("ac_radiator_temperature_c"),
        "transformer_temperature_c": inverter and inverter.get("transformer_temperature_c"),
        "dc_radiator_temperature_c": inverter and inverter.get("dc_radiator_temperature_c"),
        "rated_power_w": first(
            inverter and inverter.get("rated_power_w_from_status"),
            inverter and inverter.get("rated_power_w"),
        ),
    }

    return {
        "captured_at": captured_at,
        "source": source,
        "connection": {
            "status": "degraded" if errors else "online",
            "latency_ms": latency_ms,
            "section_errors": errors,
        },
        "identity": identity,
        "status": {
            "charger": charger,
            "inverter": inverter,
        },
        "metrics": metrics,
        "configuration": {
            "charger": charger_config,
            "inverter": inverter_config,
        } if charger_config is not None or inverter_config is not None else None,
        "raw": sections,
    }


def _raw_tenths(raw: int | None) -> float | None:
    return None if raw is None else round(raw * 0.1, 3)


def _register_pair_hex(registers: list[int] | None, index: int) -> str | None:
    if registers is None or index + 1 >= len(registers):
        return None
    return f"{registers[index]:04X}{registers[index + 1]:04X}"


def _u32_tenths(registers: list[int] | None, index: int) -> float | None:
    if registers is None or index + 1 >= len(registers):
        return None
    return round(((registers[index] << 16) | registers[index + 1]) * 0.1, 1)


def _time_value(registers: list[int] | None, index: int) -> str | None:
    if registers is None or index + 2 >= len(registers):
        return None
    return f"{registers[index]:02}:{registers[index + 1]:02}:{registers[index + 2]:02}"
