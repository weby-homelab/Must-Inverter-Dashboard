from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SERIAL_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"


def _load_dotenv(path: Path) -> None:
    """Load a small .env file without adding a dotenv dependency."""
    if not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def _float_env(name: str, default: float, minimum: float) -> float:
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(value, minimum)


def _int_env(name: str, default: int, minimum: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(value, minimum)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    public_dir: Path
    db_path: Path
    host: str
    port: int
    serial_port: str
    slave_id: int
    baudrate: int
    poll_interval: float
    sample_interval: float
    config_interval: float
    serial_timeout: float
    inter_request_delay: float
    retention_days: int
    enable_write: bool = False
    write_unlock_ttl: int = 300
    write_cooldown: float = 3.0
    max_writes_per_hour: int = 30
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    alert_low_battery_v: float = 24.6
    alert_cooldown_seconds: int = 900

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv(BASE_DIR / ".env")

        db_path = Path(os.environ.get("MUST_DB_PATH", BASE_DIR / "data" / "inverter.sqlite3"))
        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path

        return cls(
            base_dir=BASE_DIR,
            public_dir=BASE_DIR / "public",
            db_path=db_path,
            host=os.environ.get("MUST_DASH_HOST", "127.0.0.1"),
            port=_int_env("MUST_DASH_PORT", 8090, 1),
            serial_port=os.environ.get("MUST_SERIAL_PORT", DEFAULT_SERIAL_PORT),
            slave_id=_int_env("MUST_SLAVE_ID", 4, 1),
            baudrate=_int_env("MUST_BAUDRATE", 19200, 1200),
            poll_interval=_float_env("MUST_POLL_INTERVAL", 10.0, 2.0),
            sample_interval=_float_env("MUST_SAMPLE_INTERVAL", 60.0, 1.0),
            config_interval=_float_env("MUST_CONFIG_INTERVAL", 300.0, 30.0),
            serial_timeout=_float_env("MUST_SERIAL_TIMEOUT", 2.5, 0.2),
            inter_request_delay=_float_env("MUST_INTER_REQUEST_DELAY", 0.5, 0.0),
            retention_days=_int_env("MUST_RETENTION_DAYS", 730, 1),
            enable_write=_bool_env("MUST_ENABLE_WRITE", False),
            write_unlock_ttl=_int_env("MUST_WRITE_UNLOCK_TTL", 300, 30),
            write_cooldown=_float_env("MUST_WRITE_COOLDOWN", 3.0, 0.5),
            max_writes_per_hour=_int_env("MUST_MAX_WRITES_PER_HOUR", 30, 1),
            telegram_enabled=_bool_env("MUST_TELEGRAM_ENABLED", False),
            telegram_bot_token=os.environ.get("MUST_TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.environ.get("MUST_TELEGRAM_CHAT_ID", "").strip(),
            alert_low_battery_v=_float_env("MUST_ALERT_LOW_BATTERY_V", 24.6, 10.0),
            alert_cooldown_seconds=_int_env("MUST_ALERT_COOLDOWN_SECONDS", 900, 30),
        )
