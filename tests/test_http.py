import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from must_dashboard import __version__
from must_dashboard.config import Settings
from must_dashboard.http import AppContext, DashboardServer, _auto_period, _range_start
from must_dashboard.poller import EventHub
from must_dashboard.storage import Storage


class FakePoller:
    def __init__(self):
        self.status = "online"
        self.events = EventHub()

    def latest(self):
        return None

    def health(self):
        return {"status": self.status, "storage": {"sample_count": 0}}


class HttpTests(unittest.TestCase):
    def test_auto_period_uses_fine_resolution_for_short_ranges(self):
        self.assertEqual(_auto_period(3600), "minute")
        self.assertEqual(_auto_period(24 * 3600), "30m")
        self.assertEqual(_auto_period(7 * 86400), "day")

    def test_short_history_ranges_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ranges.sqlite3")
            end_ts = 1_000_000
            self.assertEqual(_range_start("1h", end_ts, storage), end_ts - 3600)
            self.assertEqual(_range_start("6h", end_ts, storage), end_ts - 6 * 3600)

    def test_healthz_reports_readiness_and_security_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            base_dir = Path(__file__).resolve().parents[1]
            settings = Settings(
                base_dir=base_dir,
                public_dir=base_dir / "public",
                db_path=Path(directory) / "test.sqlite3",
                host="127.0.0.1",
                port=0,
                serial_port="fake",
                slave_id=4,
                baudrate=19200,
                poll_interval=15,
                sample_interval=60,
                config_interval=300,
                serial_timeout=0.2,
                inter_request_delay=0,
                retention_days=1,
            )
            poller = FakePoller()
            server = DashboardServer(("127.0.0.1", 0), AppContext(settings, Storage(settings.db_path), poller))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(f"{url}/healthz", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("Content-Security-Policy", response.headers)
                    self.assertEqual(response.headers["Server"].strip(), f"MUSTPowerDesk/{__version__}")
                poller.status = "offline"
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(f"{url}/healthz", timeout=3)
                self.assertEqual(raised.exception.code, 503)
                raised.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_summary_endpoint_returns_raw_sample_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            base_dir = Path(__file__).resolve().parents[1]
            settings = Settings(
                base_dir=base_dir,
                public_dir=base_dir / "public",
                db_path=Path(directory) / "summary.sqlite3",
                host="127.0.0.1",
                port=0,
                serial_port="fake",
                slave_id=4,
                baudrate=19200,
                poll_interval=15,
                sample_interval=60,
                config_interval=300,
                serial_timeout=0.2,
                inter_request_delay=0,
                retention_days=1,
            )
            storage = Storage(settings.db_path)
            metrics = {
                "load_power_w": 100,
                "grid_power_w": -100,
                "battery_power_w": 0,
                "battery_voltage_v": 26.8,
                "grid_voltage_v": 230,
            }
            for timestamp in ("2026-09-02T10:00:00Z", "2026-09-02T10:01:00Z"):
                storage.insert_sample({
                    "captured_at": timestamp,
                    "connection": {"status": "online"},
                    "metrics": metrics,
                })
            server = DashboardServer(("127.0.0.1", 0), AppContext(settings, storage, FakePoller()))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(
                    f"{url}/api/summary?from=1788343200&to=1788343260",
                    timeout=3,
                ) as response:
                    payload = json.loads(response.read())
                self.assertEqual(payload["sample_count"], 2)
                self.assertEqual(payload["connection_status_counts"], {"online": 2})
                self.assertEqual(payload["statistics"]["load_power_w"]["max"], 100)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
