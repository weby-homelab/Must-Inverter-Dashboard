from __future__ import annotations

import copy
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Protocol

from .config import Settings
from .decode import decode_snapshot

try:
    import serial
except ImportError:  # pragma: no cover - exercised by deployment diagnostics
    serial = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)


class SerialLike(Protocol):
    is_open: bool

    def write(self, data: bytes) -> int: ...

    def read(self, size: int = 1) -> bytes: ...

    def reset_input_buffer(self) -> None: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...


class ModbusError(RuntimeError):
    """A protocol, transport, or device response error."""


def crc16(data: bytes) -> bytes:
    """Return the Modbus CRC16 in wire order (low byte first)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def _frame(slave_id: int, start: int, count: int) -> bytes:
    body = bytes((slave_id, 0x03, start >> 8, start & 0xFF, count >> 8, count & 0xFF))
    return body + crc16(body)


class ModbusRTU:
    """Minimal read-only Modbus RTU client for the MUST serial protocol."""

    RANGES = {
        "identity": (20001, 16),
        "charger_status": (15201, 21),
        "inverter_status": (25201, 79),
        "charger_config": (10101, 24),
        "inverter_config": (20101, 44),
    }

    def __init__(
        self,
        settings: Settings,
        serial_factory: Callable[..., SerialLike] | None = None,
    ) -> None:
        self.settings = settings
        self._serial_factory = serial_factory
        self._serial: SerialLike | None = None
        self._lock = threading.RLock()
        self._last_request_at = 0.0
        self._cached_configuration: dict | None = None
        self._cached_identity: dict | None = None
        self._cached_sections: dict[str, list[int]] = {}

    def _open(self) -> SerialLike:
        if self._serial is not None and self._serial.is_open:
            return self._serial
        if self._serial_factory is None:
            if serial is None:
                raise ModbusError("pyserial is not installed")
            self._serial_factory = serial.Serial  # type: ignore[assignment]

        try:
            self._serial = self._serial_factory(
                self.settings.serial_port,
                baudrate=self.settings.baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=min(self.settings.serial_timeout, 0.5),
                write_timeout=1,
                rtscts=False,
                dsrdtr=False,
            )
            # The tested CH340 interface works with both control lines low.
            for attribute in ("rts", "dtr"):
                try:
                    setattr(self._serial, attribute, False)
                except (AttributeError, OSError):
                    pass
        except Exception as exc:  # pyserial exception types vary by backend
            self._serial = None
            raise ModbusError(f"cannot open serial port: {exc}") from exc
        return self._serial

    def close(self) -> None:
        with self._lock:
            if self._serial is not None:
                try:
                    self._serial.close()
                except Exception:
                    LOGGER.debug("serial close failed", exc_info=True)
                self._serial = None

    def _read_exact(self, ser: SerialLike, size: int) -> bytes:
        deadline = time.monotonic() + self.settings.serial_timeout
        result = bytearray()
        while len(result) < size:
            chunk = ser.read(size - len(result))
            if chunk:
                result.extend(chunk)
                continue
            if time.monotonic() >= deadline:
                break
        if len(result) != size:
            raise ModbusError(f"serial response timeout: expected {size} bytes, got {len(result)}")
        return bytes(result)

    def read_holding(self, start: int, count: int) -> list[int]:
        if not 0 <= start <= 0xFFFF or not 1 <= count <=  read_count_limit():
            raise ValueError("invalid Modbus holding-register range")

        with self._lock:
            ser = self._open()
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.settings.inter_request_delay:
                time.sleep(self.settings.inter_request_delay - elapsed)

            request = _frame(self.settings.slave_id, start, count)
            try:
                ser.reset_input_buffer()
                ser.write(request)
                ser.flush()
                self._last_request_at = time.monotonic()

                header = self._read_exact(ser, 3)
                if header[0] != self.settings.slave_id:
                    raise ModbusError(f"unexpected slave id: {header[0]}")
                if header[1] == 0x83:
                    tail = self._read_exact(ser, 2)
                    response = header + tail
                    if response[-2:] != crc16(response[:-2]):
                        raise ModbusError("invalid Modbus exception CRC")
                    raise ModbusError(f"device exception code: {response[2]}")
                if header[1] != 0x03:
                    raise ModbusError(f"unexpected function: {header[1]}")

                byte_count = header[2]
                response = header + self._read_exact(ser, byte_count + 2)
            except ModbusError:
                raise
            except Exception as exc:
                raise ModbusError(f"serial read failed: {exc}") from exc

            expected_byte_count = count * 2
            if byte_count != expected_byte_count:
                raise ModbusError(
                    f"unexpected byte count: expected {expected_byte_count}, got {byte_count}"
                )
            if response[-2:] != crc16(response[:-2]):
                raise ModbusError("invalid Modbus response CRC")

            payload = response[3:-2]
            return [int.from_bytes(payload[index:index + 2], "big") for index in range(0, len(payload), 2)]

    def poll_once(self, include_config: bool) -> dict:
        """Read the known safe ranges and decode a complete snapshot."""
        with self._lock:
            sections: dict[str, list[int]] = {}
            errors: dict[str, str] = {}
            ranges = ("identity", "charger_status", "inverter_status")
            if include_config or self._cached_configuration is None:
                ranges += ("charger_config", "inverter_config")

            started = time.monotonic()
            for section in ranges:
                start, count = self.RANGES[section]
                try:
                    sections[section] = self.read_holding(start, count)
                    self._cached_sections[section] = copy.deepcopy(sections[section])
                except ModbusError as exc:
                    errors[section] = str(exc)
                    LOGGER.warning("Modbus read failed for %s: %s", section, exc)

            if "inverter_status" not in sections and "charger_status" not in sections:
                self.close()
                detail = "; ".join(f"{key}: {value}" for key, value in errors.items())
                raise ModbusError(detail or "no status range returned")

            # Configuration and identity change rarely. Keep their last valid
            # frames visible while the fast status cycle continues.
            for section in ("identity", "charger_config", "inverter_config"):
                if section not in sections and section in self._cached_sections:
                    sections[section] = copy.deepcopy(self._cached_sections[section])

            captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            snapshot = decode_snapshot(
                sections=sections,
                captured_at=captured_at,
                source={
                    "port": self.settings.serial_port,
                    "slave_id": self.settings.slave_id,
                    "baudrate": self.settings.baudrate,
                },
                errors=errors,
                latency_ms=round((time.monotonic() - started) * 1000, 1),
            )

            if snapshot.get("configuration") is not None:
                self._cached_configuration = copy.deepcopy(snapshot["configuration"])
            elif self._cached_configuration is not None:
                snapshot["configuration"] = copy.deepcopy(self._cached_configuration)

            if snapshot.get("identity"):
                self._cached_identity = copy.deepcopy(snapshot["identity"])
            elif self._cached_identity is not None:
                snapshot["identity"] = copy.deepcopy(self._cached_identity)

            return snapshot


def read_count_limit() -> int:
    # Modbus RTU function 03 permits at most 125 registers per request.
    return 125
