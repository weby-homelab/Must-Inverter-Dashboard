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
                CREATE TABLE IF NOT EXISTS config_audit (
                    id INTEGER PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    created_ts INTEGER NOT NULL,
                    client_ip TEXT NOT NULL,
                    param_key TEXT NOT NULL,
                    tier INTEGER NOT NULL,
                    register_address INTEGER NOT NULL,
                    old_raw INTEGER,
                    new_raw INTEGER NOT NULL,
                    verified_raw INTEGER,
                    old_value_json TEXT,
                    new_value_json TEXT,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    error_message TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_config_audit_created_ts
                    ON config_audit(created_ts);
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
        period = {"1m": "minute", "30min": "30m"}.get(period, period)
        if period == "raw":
            return self._raw_history(start_ts, end_ts, max_raw_points)
        if period not in {"minute", "30m", "hour", "day", "week", "month"}:
            raise ValueError("period must be raw, minute, 30m, hour, day, week, or month")

        bucket_expression = {
            "minute": "strftime('%Y-%m-%dT%H:%M:00Z', captured_at)",
            "30m": (
                "strftime('%Y-%m-%dT%H:', captured_at) || "
                "printf('%02d:00Z', (CAST(strftime('%M', captured_at) AS INTEGER) / 30) * 30)"
            ),
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

    def summary(
        self,
        start_ts: int,
        end_ts: int,
        sample_interval_seconds: float = 60.0,
    ) -> dict[str, Any]:
        selected = ", ".join(("captured_at", "captured_ts", "connection_status", *METRIC_COLUMNS))
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                f"SELECT {selected} FROM samples "
                "WHERE captured_ts >= ? AND captured_ts <= ? ORDER BY captured_ts",
                (start_ts, end_ts),
            ).fetchall()

        points = [dict(row) for row in rows]
        sample_count = len(points)
        if not points:
            return {
                "from": _iso_from_ts(start_ts),
                "to": _iso_from_ts(end_ts),
                "observed_from": None,
                "observed_to": None,
                "sample_count": 0,
                "expected_samples": 0,
                "coverage_percent": 0,
                "gap_count": 0,
                "largest_gap_seconds": 0,
                "integrated_seconds": 0,
                "energy_coverage_percent": 0,
                "connection_status_counts": {},
                "grid_unavailable_samples": 0,
                "grid_unavailable_runs": 0,
                "pv_active_samples": 0,
                "missing_by_metric": {column: 0 for column in METRIC_COLUMNS},
                "statistics": {column: _empty_metric_stats() for column in METRIC_COLUMNS},
                "energy": _empty_energy_summary(),
            }

        def values_for(column: str) -> list[float]:
            return [float(point[column]) for point in points if point[column] is not None]

        def metric_stats(column: str) -> dict[str, int | float | None]:
            values = values_for(column)
            if not values:
                return _empty_metric_stats(missing=sample_count)
            return {
                "samples": len(values),
                "missing": sample_count - len(values),
                "nonzero_samples": sum(value != 0 for value in values),
                "average": _number(sum(values) / len(values)),
                "min": _number(min(values)),
                "max": _number(max(values)),
            }

        statistics = {column: metric_stats(column) for column in METRIC_COLUMNS}
        first_ts = int(points[0]["captured_ts"])
        last_ts = int(points[-1]["captured_ts"])
        span_seconds = max(0, last_ts - first_ts)
        interval = max(float(sample_interval_seconds), 1.0)
        expected_samples = max(1, int(span_seconds / interval) + 1)
        gap_threshold = max(120.0, interval * 2)
        integration_limit = max(900.0, interval * 15)
        gap_count = 0
        largest_gap = 0.0
        integrated_seconds = 0.0
        energy = _empty_energy_summary()
        grid_unavailable_samples = 0
        grid_unavailable_runs = 0
        previous_grid_unavailable = False

        statuses: dict[str, int] = {}
        for point in points:
            status = str(point["connection_status"])
            statuses[status] = statuses.get(status, 0) + 1
            grid_voltage = point["grid_voltage_v"]
            grid_unavailable = grid_voltage is not None and float(grid_voltage) <= 0
            if grid_unavailable:
                grid_unavailable_samples += 1
                if not previous_grid_unavailable:
                    grid_unavailable_runs += 1
            previous_grid_unavailable = grid_unavailable
        for first, second in zip(points, points[1:]):
            delta = int(second["captured_ts"]) - int(first["captured_ts"])
            if delta <= 0:
                continue
            if delta > gap_threshold:
                gap_count += 1
                largest_gap = max(largest_gap, float(delta))
            if delta > integration_limit:
                continue
            integrated_seconds += delta
            for column, positive, negative in (
                ("load_power_w", True, False),
                ("pv_power_w", True, False),
                ("grid_power_w", False, True),
                ("battery_power_w", True, True),
            ):
                first_value = first[column]
                second_value = second[column]
                if first_value is None or second_value is None:
                    continue
                average = (float(first_value) + float(second_value)) / 2
                if column == "load_power_w":
                    energy["load_kwh"] += max(average, 0) * delta / 3_600_000
                elif column == "pv_power_w":
                    energy["pv_kwh"] += max(average, 0) * delta / 3_600_000
                elif column == "grid_power_w":
                    energy["grid_import_kwh"] += max(-average, 0) * delta / 3_600_000
                    energy["grid_export_kwh"] += max(average, 0) * delta / 3_600_000
                elif positive and negative:
                    energy["battery_discharge_kwh"] += max(average, 0) * delta / 3_600_000
                    energy["battery_charge_kwh"] += max(-average, 0) * delta / 3_600_000

        energy = {key: round(value, 3) for key, value in energy.items()}
        return {
            "from": _iso_from_ts(start_ts),
            "to": _iso_from_ts(end_ts),
            "observed_from": points[0]["captured_at"],
            "observed_to": points[-1]["captured_at"],
            "sample_count": sample_count,
            "expected_samples": expected_samples,
            "coverage_percent": _number(min(100, sample_count / expected_samples * 100)),
            "gap_count": gap_count,
            "largest_gap_seconds": int(largest_gap),
            "integrated_seconds": int(integrated_seconds),
            "energy_coverage_percent": _number(
                min(100, integrated_seconds / span_seconds * 100) if span_seconds else 100
            ),
            "connection_status_counts": statuses,
            "grid_unavailable_samples": grid_unavailable_samples,
            "grid_unavailable_runs": grid_unavailable_runs,
            "pv_active_samples": sum(
                float(point["pv_power_w"]) > 0 for point in points if point["pv_power_w"] is not None
            ),
            "missing_by_metric": {
                column: int(statistics[column]["missing"] or 0) for column in METRIC_COLUMNS
            },
            "statistics": statistics,
            "energy": energy,
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

    def insert_audit(
        self,
        *,
        created_at: str,
        client_ip: str,
        param_key: str,
        tier: int,
        register_address: int,
        old_raw: int | None,
        new_raw: int,
        verified_raw: int | None,
        old_value: Any,
        new_value: Any,
        status: str,
        reason: str,
        error_message: str | None = None,
    ) -> int:
        created_ts = int(datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp())
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO config_audit (
                    created_at, created_ts, client_ip, param_key, tier, register_address,
                    old_raw, new_raw, verified_raw, old_value_json, new_value_json,
                    status, reason, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    created_ts,
                    client_ip,
                    param_key,
                    tier,
                    register_address,
                    old_raw,
                    new_raw,
                    verified_raw,
                    json.dumps(old_value, ensure_ascii=False) if old_value is not None else None,
                    json.dumps(new_value, ensure_ascii=False) if new_value is not None else None,
                    status,
                    reason,
                    error_message,
                ),
            )
            return int(cursor.lastrowid)

    def list_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        clamped = max(1, min(int(limit), 200))
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM config_audit ORDER BY created_ts DESC, id DESC LIMIT ?",
                (clamped,),
            ).fetchall()
        return [_audit_row_to_dict(row) for row in rows]

    def get_audit(self, audit_id: int) -> dict[str, Any] | None:
        with self._lock, self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM config_audit WHERE id = ?",
                (int(audit_id),),
            ).fetchone()
        return _audit_row_to_dict(row) if row else None

    def outages(
        self,
        start_ts: int,
        end_ts: int,
        *,
        grid_threshold_v: float = 50.0,
        sample_interval_seconds: float = 60.0,
    ) -> dict[str, Any]:
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                "SELECT captured_at, captured_ts, grid_voltage_v, battery_voltage_v, load_power_w "
                "FROM samples WHERE captured_ts >= ? AND captured_ts <= ? ORDER BY captured_ts",
                (start_ts, end_ts),
            ).fetchall()

        interval = max(float(sample_interval_seconds), 1.0)
        max_gap = max(900.0, interval * 15)
        ongoing_grace = max(600.0, interval * 5)

        events: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None

        def close_current(ended_at: str | None = None, ended_ts: int | None = None, *, ongoing: bool = False) -> None:
            nonlocal current
            if current is None:
                return
            stop_ts = ended_ts if ended_ts is not None else current["last_ts"]
            stop_at = ended_at if ended_at is not None else current["last_at"]
            duration = max(0, int(stop_ts - current["started_ts"]))
            if not ongoing and duration == 0:
                duration = int(interval)
            events.append({
                "started_at": current["started_at"],
                "ended_at": None if ongoing else stop_at,
                "ongoing": ongoing,
                "duration_seconds": duration,
                "sample_count": current["sample_count"],
                "min_battery_voltage_v": _number(current["min_battery_v"]),
                "max_load_power_w": _number(current["max_load_w"]),
            })
            current = None

        for row in rows:
            ts = int(row["captured_ts"])
            at = str(row["captured_at"])
            grid_v = row["grid_voltage_v"]
            batt_v = row["battery_voltage_v"]
            load_w = row["load_power_w"]

            if current is not None and ts - current["last_ts"] > max_gap:
                close_current()

            is_outage = grid_v is not None and float(grid_v) < grid_threshold_v
            if is_outage:
                if current is None:
                    current = {
                        "started_at": at,
                        "started_ts": ts,
                        "last_at": at,
                        "last_ts": ts,
                        "sample_count": 1,
                        "min_battery_v": float(batt_v) if batt_v is not None else None,
                        "max_load_w": float(load_w) if load_w is not None else None,
                    }
                else:
                    current["last_at"] = at
                    current["last_ts"] = ts
                    current["sample_count"] += 1
                    if batt_v is not None:
                        val = float(batt_v)
                        current["min_battery_v"] = val if current["min_battery_v"] is None else min(current["min_battery_v"], val)
                    if load_w is not None:
                        val = float(load_w)
                        current["max_load_w"] = val if current["max_load_w"] is None else max(current["max_load_w"], val)
            elif current is not None:
                close_current(ended_at=at, ended_ts=ts, ongoing=False)

        if current is not None:
            is_ongoing = (end_ts - current["last_ts"]) <= ongoing_grace
            close_current(
                ended_at=_iso_from_ts(end_ts) if is_ongoing else current["last_at"],
                ended_ts=end_ts if is_ongoing else current["last_ts"],
                ongoing=is_ongoing,
            )

        total_outage_seconds = sum(event["duration_seconds"] for event in events)
        ongoing_flag = any(event["ongoing"] for event in events)
        events.reverse()
        return {
            "from": _iso_from_ts(start_ts),
            "to": _iso_from_ts(end_ts),
            "total_outages": len(events),
            "total_outage_seconds": int(total_outage_seconds),
            "ongoing": ongoing_flag,
            "events": events,
        }


def _audit_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "created_at": row["created_at"],
        "created_ts": int(row["created_ts"]),
        "client_ip": row["client_ip"],
        "param_key": row["param_key"],
        "tier": int(row["tier"]),
        "register_address": int(row["register_address"]),
        "old_raw": row["old_raw"],
        "new_raw": int(row["new_raw"]),
        "verified_raw": row["verified_raw"],
        "old_value": json.loads(row["old_value_json"]) if row["old_value_json"] is not None else None,
        "new_value": json.loads(row["new_value_json"]) if row["new_value_json"] is not None else None,
        "status": row["status"],
        "reason": row["reason"],
        "error_message": row["error_message"],
    }


def _number(value: Any) -> int | float | None:
    if value is None:
        return None
    numeric = float(value)
    return int(numeric) if numeric.is_integer() else round(numeric, 3)


def _empty_metric_stats(*, missing: int = 0) -> dict[str, int | float | None]:
    return {
        "samples": 0,
        "missing": missing,
        "nonzero_samples": 0,
        "average": None,
        "min": None,
        "max": None,
    }


def _empty_energy_summary() -> dict[str, float]:
    return {
        "load_kwh": 0.0,
        "pv_kwh": 0.0,
        "grid_import_kwh": 0.0,
        "grid_export_kwh": 0.0,
        "battery_charge_kwh": 0.0,
        "battery_discharge_kwh": 0.0,
    }


def _iso_from_ts(value: Any) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(int(value), timezone.utc).isoformat().replace("+00:00", "Z")
