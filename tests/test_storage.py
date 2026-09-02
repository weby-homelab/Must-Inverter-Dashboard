import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from must_dashboard.storage import METRIC_COLUMNS, Storage


def snapshot(captured_at, load_power):
    return {
        "captured_at": captured_at,
        "connection": {"status": "online"},
        "metrics": {
            "battery_voltage_v": 26.8,
            "pv_voltage_v": 0,
            "pv_power_w": 0,
            "inverter_voltage_v": 229.7,
            "grid_voltage_v": 230.6,
            "inverter_power_w": -22,
            "grid_power_w": -380,
            "load_power_w": load_power,
            "load_percent": 16,
            "inverter_frequency_hz": 49.95,
            "grid_frequency_hz": 49.95,
            "battery_power_w": 0,
        },
    }


class StorageTests(unittest.TestCase):
    def test_insert_latest_stats_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Storage(Path(directory) / "samples.sqlite3")
            store.insert_sample(snapshot("2026-09-02T10:00:00Z", 100))
            store.insert_sample(snapshot("2026-09-02T10:30:00Z", 300))
            self.assertEqual(store.latest_payload()["metrics"]["load_power_w"], 300)
            self.assertEqual(store.stats()["sample_count"], 2)
            history = store.history(1788340000, 1788350000, "hour")
            self.assertEqual(len(history["points"]), 1)
            self.assertEqual(history["points"][0]["load_power_w"], 200)
            self.assertEqual(history["points"][0]["load_power_min_w"], 100)
            self.assertEqual(history["points"][0]["load_power_max_w"], 300)

    def test_existing_database_gets_new_metric_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.sqlite3"
            with closing(sqlite3.connect(path)) as connection:
                connection.execute(
                    "CREATE TABLE samples (id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, "
                    "captured_ts INTEGER NOT NULL, connection_status TEXT NOT NULL, "
                    "battery_voltage_v REAL, payload_json TEXT NOT NULL)"
                )
                connection.commit()
            Storage(path)
            with closing(sqlite3.connect(path)) as connection:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(samples)")}
            self.assertTrue(set(METRIC_COLUMNS).issubset(columns))

    def test_raw_history_keeps_latest_points_when_limited(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Storage(Path(directory) / "samples.sqlite3")
            for minute, load in ((0, 100), (1, 200), (2, 300)):
                store.insert_sample(snapshot(f"2026-09-02T10:{minute:02}:00Z", load))
            history = store.history(1788340000, 1788350000, "raw", max_raw_points=2)
            self.assertTrue(history["truncated"])
            self.assertEqual([point["load_power_w"] for point in history["points"]], [200, 300])

    def test_minute_and_half_hour_buckets(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Storage(Path(directory) / "samples.sqlite3")
            for timestamp, load in (
                ("2026-09-02T10:00:05Z", 100),
                ("2026-09-02T10:00:55Z", 200),
                ("2026-09-02T10:01:00Z", 300),
                ("2026-09-02T10:30:00Z", 400),
            ):
                store.insert_sample(snapshot(timestamp, load))
            minute = store.history(1788340000, 1788350000, "minute")
            half_hour = store.history(1788340000, 1788350000, "30m")
            self.assertEqual([point["captured_at"] for point in minute["points"]], [
                "2026-09-02T10:00:00Z",
                "2026-09-02T10:01:00Z",
                "2026-09-02T10:30:00Z",
            ])
            self.assertEqual([point["captured_at"] for point in half_hour["points"]], [
                "2026-09-02T10:00:00Z",
                "2026-09-02T10:30:00Z",
            ])
            self.assertEqual(minute["points"][0]["load_power_w"], 150)


if __name__ == "__main__":
    unittest.main()
