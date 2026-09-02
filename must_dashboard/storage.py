from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


METRIC_COLUMNS = (
    "battery_voltage_v",
    "pv_voltage_v",
    "pv_current_a",
    "pv_power_w",
    "inverter_voltage_v",
    "grid_voltage_v",
    "bus_voltage_v",
    "inverter_current_a",
    "grid_current_a",
    "load_current_a",
    "inverter_power_w",
    "grid_power_w",
    "load_power_w",
    "load_percent",
    "inverter_frequency_hz",
    "grid_frequency_hz",
    "battery_power_w",
    "ac_radiator_temperature_c",
    "transformer_temperature_c",
    "dc_radiator_temperature_c",
)


class Storage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS samples (
                    id INTEGER PRIMARY KEY,
                    captured_at TEXT NOT NULL,
                    captured_ts INTEGER NOT NULL,
                    connection_status TEXT NOT NULL,
                    battery_voltage_v REAL,
                    pv_voltage_v REAL,
                    pv_current_a REAL,
                    pv_power_w REAL,
                    inverter_voltage_v REAL,
                    grid_voltage_v REAL,
                    bus_voltage_v REAL,
                    inverter_current_a REAL,
                    grid_current_a REAL,
                    load_current_a REAL,
                    inverter_power_w REAL,
                    grid_power_w REAL,
                    load_power_w REAL,
                    load_percent REAL,
                    inverter_frequency_hz REAL,
                    grid_frequency_hz REAL,
                    battery_power_w REAL,
                    ac_radiator_temperature_c REAL,
                    transformer_temperature_c REAL,
                    dc_radiator_temperature_c REAL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_samples_captured_ts
                    ON samples(captured_ts);
                """
            )
            existing_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(samples)").fetchall()
            }
            for column in METRIC_COLUMNS:
                if column not in existing_columns:
                    connection.execute(f"ALTER TABLE samples ADD COLUMN {column} REAL")

    def insert_sample(self, snapshot: dict[str, Any]) -> None:
        metrics = snapshot.get("metrics", {})
        captured_at = snapshot["captured_at"]
        captured_ts = int(datetime.fromisoformat(captured_at.replace("Z", "+00:00")).timestamp())
        values = [metrics.get(column) for column in METRIC_COLUMNS]
        with self._lock, self._connection() as connection:
            connection.execute(
                f"INSERT INTO samples (captured_at, captured_ts, connection_status, "
                f"{', '.join(METRIC_COLUMNS)}, payload_json) "
                f"VALUES (?, ?, ?, {', '.join('?' for _ in METRIC_COLUMNS)}, ?)",
                [
                    captured_at,
                    captured_ts,
                    snapshot.get("connection", {}).get("status", "unknown"),
                    *values,
                    json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")),
                ],
            )

    def latest_payload(self) -> dict[str, Any] | None:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM samples ORDER BY captured_ts DESC, id DESC LIMIT 1"
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def last_sample_ts(self) -> int | None:
        with self._lock, self._connection() as connection:
            row = connection.execute("SELECT MAX(captured_ts) AS captured_ts FROM samples").fetchone()
        return int(row["captured_ts"]) if row and row["captured_ts"] is not None else None

    def stats(self) -> dict[str, Any]:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count, MIN(captured_ts) AS oldest, MAX(captured_ts) AS newest FROM samples"
            ).fetchone()
        return {
            "sample_count": int(row["count"]),
            "oldest_at": _iso_from_ts(row["oldest"]),
            "newest_at": _iso_from_ts(row["newest"]),
        }

    def prune(self, retention_days: int) -> int:
        cutoff = int(time.time()) - retention_days * 86400
        with self._lock, self._connection() as connection:
            cursor = connection.execute("DELETE FROM samples WHERE captured_ts < ?", (cutoff,))
            return cursor.rowcount

    def history(
        self,
        start_ts: int,
        end_ts: int,
        period: str,
        max_raw_points: int = 20000,
    ) -> dict[str, Any]:
        if period == "raw":
            return self._raw_history(start_ts, end_ts, max_raw_points)
        if period not in {"hour", "day", "week", "month"}:
            raise ValueError("period must be raw, hour, day, week, or month")

        bucket_expression = {
            "hour": "strftime('%Y-%m-%dT%H:00:00Z', captured_at)",
            "day": "strftime('%Y-%m-%dT00:00:00Z', captured_at)",
            "week": (
                "strftime('%Y-%m-%dT00:00:00Z', date(captured_at, "
                "'-' || ((CAST(strftime('%w', captured_at) AS INTEGER) + 6) % 7) || ' days'))"
            ),
            "month": "strftime('%Y-%m-01T00:00:00Z', captured_at)",
        }[period]
        average_columns = ", ".join(f"AVG({column}) AS {column}" for column in METRIC_COLUMNS)
        min_max_columns = ", MIN(load_power_w) AS load_power_min_w, MAX(load_power_w) AS load_power_max_w"
        query = f"""
            SELECT bucket, COUNT(*) AS samples, {average_columns}{min_max_columns}
            FROM (
                SELECT captured_at, {', '.join(METRIC_COLUMNS)}, {bucket_expression} AS bucket
                FROM samples
                WHERE captured_ts >= ? AND captured_ts <= ?
            )
            GROUP BY bucket
            ORDER BY bucket
        """
        with self._lock, self._connection() as connection:
            rows = connection.execute(query, (start_ts, end_ts)).fetchall()

        points = []
        for row in rows:
            point = {"captured_at": row["bucket"], "samples": row["samples"]}
            for column in METRIC_COLUMNS:
                point[column] = _number(row[column])
            point["load_power_min_w"] = _number(row["load_power_min_w"])
            point["load_power_max_w"] = _number(row["load_power_max_w"])
            points.append(point)
        return {
            "from": _iso_from_ts(start_ts),
            "to": _iso_from_ts(end_ts),
            "period": period,
            "truncated": False,
            "points": points,
        }

    def _raw_history(self, start_ts: int, end_ts: int, limit: int) -> dict[str, Any]:
        selected = ", ".join(("captured_at", "captured_ts", "connection_status", *METRIC_COLUMNS))
        with self._lock, self._connection() as connection:
            count_row = connection.execute(
                "SELECT COUNT(*) AS count FROM samples WHERE captured_ts >= ? AND captured_ts <= ?",
                (start_ts, end_ts),
            ).fetchone()
            rows = connection.execute(
                f"SELECT {selected} FROM ("
                f"SELECT {selected} FROM samples WHERE captured_ts >= ? AND captured_ts <= ? "
                "ORDER BY captured_ts DESC LIMIT ?"
                ") ORDER BY captured_ts",
                (start_ts, end_ts, limit),
            ).fetchall()

        truncated = int(count_row["count"]) > limit
        points = []
        for row in rows[:limit]:
            point = {
                "captured_at": row["captured_at"],
                "captured_ts": row["captured_ts"],
                "connection_status": row["connection_status"],
            }
            point.update({column: _number(row[column]) for column in METRIC_COLUMNS})
            points.append(point)
        return {
            "from": _iso_from_ts(start_ts),
            "to": _iso_from_ts(end_ts),
            "period": "raw",
            "truncated": truncated,
            "points": points,
        }


def _number(value: Any) -> int | float | None:
    if value is None:
        return None
    numeric = float(value)
    return int(numeric) if numeric.is_integer() else round(numeric, 3)


def _iso_from_ts(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat().replace("+00:00", "Z")
