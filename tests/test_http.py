import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from must_dashboard.config import Settings
from must_dashboard.http import AppContext, DashboardServer, _auto_period
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
                poller.status = "offline"
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(f"{url}/healthz", timeout=3)
                self.assertEqual(raised.exception.code, 503)
                raised.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
