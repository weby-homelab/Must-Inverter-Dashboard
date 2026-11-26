import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from must_dashboard import __version__
from must_dashboard.config import Settings
from must_dashboard.control import ControlManager
from must_dashboard.decode import decode_snapshot
from must_dashboard.http import AppContext, DashboardServer, _auto_period, _range_start
from must_dashboard.poller import EventHub
from must_dashboard.storage import Storage


class FakePoller:
    def __init__(self, snapshot=None):
        self.status = "online"
        self.events = EventHub()
        self._snapshot = snapshot
        self.writes = []

    def latest(self):
        return self._snapshot

    def health(self):
        return {"status": self.status, "storage": {"sample_count": 0}}

    def write_register(self, address, value, *, verify=True):
        self.writes.append((address, value))
        if self._snapshot and 20101 <= address <= 20144:
            self._snapshot["raw"]["inverter_config"][address - 20101] = value
        return {"address": address, "before": 3, "requested": value, "after": value, "status": "verified", "written": True}

    def refresh_now(self, *, include_config=True):
        return self._snapshot


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

    def test_outages_and_control_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            base_dir = Path(__file__).resolve().parents[1]
            settings = Settings(
                base_dir=base_dir,
                public_dir=base_dir / "public",
                db_path=Path(directory) / "control.sqlite3",
                host="127.0.0.1",
                port=0,
                serial_port="fake",
                slave_id=4,
                baudrate=19200,
                poll_interval=10,
                sample_interval=60,
                config_interval=300,
                serial_timeout=0.2,
                inter_request_delay=0,
                retention_days=1,
                enable_write=True,
                write_cooldown=0.5,
            )
            storage = Storage(settings.db_path)
            storage.insert_sample({
                "captured_at": "2026-11-26T10:00:00Z",
                "connection": {"status": "online"},
                "metrics": {"grid_voltage_v": 0.0, "battery_voltage_v": 26.2, "load_power_w": 250},
            })
            chg_cfg = [1, 250, 270, 288, 170, 170, 300, 600, 100, 1, 200, 0, 24, 1, 0, 0, 0, 0, 288, 150, 60, 120, 30, 0]
            inv_cfg = [1, 2200, 5000, 0, 1, 1, 1, 0, 3, 0, 1, 0, 136, 136, 0, 0, 241, 244, 268, 0, 250, 270, 288, 24, 300, 200, 240, 300, 1, 200, 250, 600, 0, 0, 0, 0, 0, 0, 0, 0, 0, 35, 2, 0]
            inv_status = [0] * 79
            inv_status[74] = 24
            snap = decode_snapshot(
                sections={"charger_config": chg_cfg, "inverter_config": inv_cfg, "inverter_status": inv_status},
                captured_at="2026-11-26T10:01:00Z",
                source={"port": "fake", "slave_id": 4, "baudrate": 19200},
                errors={},
                latency_ms=10.0,
            )
            poller = FakePoller(snapshot=snap)
            control = ControlManager(settings, poller, storage)
            server = DashboardServer(("127.0.0.1", 0), AppContext(settings, storage, poller, control))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                with urllib.request.urlopen(f"{url}/api/outages?from=1795687100&to=1795687300", timeout=3) as resp:
                    outages = json.loads(resp.read())
                self.assertEqual(outages["total_outages"], 1)

                # Missing X-Requested-With header must be rejected with 403
                req_no_csrf = urllib.request.Request(f"{url}/api/control/unlock", data=b"{}", method="POST")
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(req_no_csrf, timeout=3)
                self.assertEqual(raised.exception.code, 403)
                raised.exception.close()

                # Unlock -> Preview -> Write -> Audit
                def post(path, body, token=None):
                    headers = {"Content-Type": "application/json", "X-Requested-With": "MUSTPowerDesk"}
                    if token:
                        headers["X-Control-Token"] = token
                    req = urllib.request.Request(
                        f"{url}{path}",
                        data=json.dumps(body).encode("utf-8"),
                        headers=headers,
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=3) as r:
                        return json.loads(r.read())

                unlocked = post("/api/control/unlock", {})
                token = unlocked["token"]
                preview = post("/api/control/preview", {"changes": {"energy_use_mode": 1}})
                self.assertTrue(preview["has_changes"])
                written = post("/api/control/write", {"changes": {"energy_use_mode": 1}}, token=token)
                self.assertEqual(written["written_count"], 1)
                self.assertEqual(poller.writes, [(20109, 1)])

                with urllib.request.urlopen(f"{url}/api/control/audit?limit=10", timeout=3) as resp:
                    audit = json.loads(resp.read())
                self.assertEqual(len(audit["entries"]), 1)
                self.assertEqual(audit["entries"][0]["status"], "verified")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
