import unittest
from pathlib import Path

from must_dashboard.alerts import AlertManager
from must_dashboard.config import Settings


def alert_settings(*, enabled=True, low_v=24.6, cooldown=900):
    return Settings(
        base_dir=Path("/tmp"),
        public_dir=Path("/tmp"),
        db_path=Path("/tmp/test.sqlite3"),
        host="127.0.0.1",
        port=8090,
        serial_port="mock",
        slave_id=4,
        baudrate=19200,
        poll_interval=10,
        sample_interval=60,
        config_interval=300,
        serial_timeout=0.5,
        inter_request_delay=0.0,
        retention_days=30,
        telegram_enabled=enabled,
        telegram_bot_token="secret-bot-token",
        telegram_chat_id="123456",
        alert_low_battery_v=low_v,
        alert_cooldown_seconds=cooldown,
    )


def snap(grid_v=230.0, batt_v=26.5, load_w=300, chg_flags=None):
    return {
        "metrics": {"grid_voltage_v": grid_v, "battery_voltage_v": batt_v, "load_power_w": load_w},
        "status": {
            "charger": {"error_flags": chg_flags or []},
            "inverter": {"error_flags": []},
        },
    }


class AlertTests(unittest.TestCase):
    def test_grid_outage_debounce_and_restore(self):
        sent = []
        now = [100.0]
        mgr = AlertManager(alert_settings(), sender=sent.append, clock=lambda: now[0])
        mgr.evaluate_snapshot(snap(grid_v=230.0))
        mgr.evaluate_snapshot(snap(grid_v=0.0))  # 1st poll: debounce
        self.assertEqual(sent, [])
        now[0] = 110.0
        mgr.evaluate_snapshot(snap(grid_v=0.0))  # 2nd poll: triggers
        self.assertEqual(len(sent), 1)
        self.assertIn("Grid lost", sent[0])

        now[0] = 410.0
        mgr.evaluate_snapshot(snap(grid_v=230.0))
        mgr.evaluate_snapshot(snap(grid_v=230.0))
        self.assertEqual(len(sent), 2)
        self.assertIn("Grid restored", sent[1])
        self.assertIn("5 min", sent[1])

    def test_low_battery_hysteresis_and_offline(self):
        sent = []
        now = [1000.0]
        mgr = AlertManager(alert_settings(low_v=24.6, cooldown=60), sender=sent.append, clock=lambda: now[0])
        mgr.evaluate_snapshot(snap(batt_v=24.5))
        mgr.evaluate_snapshot(snap(batt_v=24.4))
        self.assertEqual(len(sent), 1)
        self.assertIn("Low battery", sent[0])

        # Re-arms only after +0.4V hysteresis (25.0V)
        now[0] = 1200.0
        mgr.evaluate_snapshot(snap(batt_v=24.8))
        mgr.evaluate_snapshot(snap(batt_v=24.5))
        self.assertEqual(len(sent), 1)

        mgr.evaluate_snapshot(snap(batt_v=25.1))
        mgr.evaluate_snapshot(snap(batt_v=24.5))
        self.assertEqual(len(sent), 2)

        mgr.evaluate_health({"status": "offline", "consecutive_failures": 3, "last_error": "timeout"})
        mgr.evaluate_health({"status": "online", "consecutive_failures": 0})
        self.assertEqual(len(sent), 4)
        self.assertIn("offline", sent[2])
        self.assertIn("recovered", sent[3])

    def test_ignores_info_pv_low_flag(self):
        sent = []
        mgr = AlertManager(alert_settings(), sender=sent.append)
        mgr.evaluate_snapshot(snap(chg_flags=[{"bit": 5, "code": "pv_voltage_low", "severity": "info"}]))
        self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
