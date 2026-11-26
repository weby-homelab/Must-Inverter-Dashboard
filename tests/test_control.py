import tempfile
import unittest
from pathlib import Path

from must_dashboard.config import Settings
from must_dashboard.control import ControlError, ControlManager
from must_dashboard.decode import decode_snapshot
from must_dashboard.storage import Storage


class MockPoller:
    def __init__(self, status="online"):
        self.status = status
        self.writes = []
        self.charger_cfg = [1, 250, 270, 288, 170, 170, 300, 600, 100, 1, 200, 0, 24, 1, 0, 0, 0, 0, 288, 150, 60, 120, 30, 0]
        self.inverter_cfg = [
            1, 2200, 5000, 0, 1, 1, 1, 0, 3, 0, 1, 0, 136, 136, 0, 0, 241, 244, 268, 0,
            250, 270, 288, 24, 300, 200, 240, 300, 1, 200, 250, 600, 0, 0, 0, 0, 0, 0, 0, 0, 0, 35, 2, 0
        ]
        self.inverter_status = [0] * 79
        self.inverter_status[74] = 24

    def health(self):
        return {"status": self.status}

    def latest(self):
        if self.status == "starting":
            return None
        return decode_snapshot(
            sections={
                "inverter_status": self.inverter_status,
                "charger_config": list(self.charger_cfg),
                "inverter_config": list(self.inverter_cfg),
            },
            captured_at="2026-11-26T14:00:00Z",
            source={"port": "mock", "slave_id": 4, "baudrate": 19200},
            errors={},
            latency_ms=50.0,
        )

    def write_register(self, address, value, *, verify=True):
        self.writes.append((address, value))
        if 20101 <= address <= 20144:
            idx = address - 20101
            before = self.inverter_cfg[idx]
            if before == value:
                return {"address": address, "before": before, "requested": value, "after": before, "status": "noop", "written": False}
            self.inverter_cfg[idx] = value
            return {"address": address, "before": before, "requested": value, "after": value, "status": "verified", "written": True}
        if 10101 <= address <= 10124:
            idx = address - 10101
            before = self.charger_cfg[idx]
            if before == value:
                return {"address": address, "before": before, "requested": value, "after": before, "status": "noop", "written": False}
            self.charger_cfg[idx] = value
            return {"address": address, "before": before, "requested": value, "after": value, "status": "verified", "written": True}
        raise AssertionError(f"unexpected address {address}")

    def refresh_now(self, *, include_config=True):
        return self.latest()


def make_settings(db_path, *, enable_write=True, write_cooldown=3.0, unlock_ttl=300):
    return Settings(
        base_dir=Path("/tmp"),
        public_dir=Path("/tmp"),
        db_path=db_path,
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
        enable_write=enable_write,
        write_unlock_ttl=unlock_ttl,
        write_cooldown=write_cooldown,
        max_writes_per_hour=20,
    )


class ControlTests(unittest.TestCase):
    def test_write_disabled_blocks_unlock_and_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ctrl.sqlite3")
            ctrl = ControlManager(make_settings(storage.path, enable_write=False), MockPoller(), storage)
            self.assertFalse(ctrl.status()["write_enabled"])
            with self.assertRaises(ControlError) as ctx:
                ctrl.unlock()
            self.assertEqual(ctx.exception.status_code, 403)

    def test_allowlist_and_tier2_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ctrl.sqlite3")
            ctrl = ControlManager(make_settings(storage.path), MockPoller(), storage)
            with self.assertRaises(ControlError):
                ctrl.preview({"arbitrary_reg": 1})
            with self.assertRaises(ControlError):
                ctrl.preview({"grid_max_charger_current_a": 65.0})
            with self.assertRaises(ControlError):
                ctrl.preview({"grid_max_charger_current_a": 50.0, "max_combine_charger_current_a": 40.0})
            # Tier 2 ordering: normal_voltage_point_v (25.0) >= start_sell_voltage_point_v (24.5) must fail
            with self.assertRaises(ControlError):
                ctrl.preview({"normal_voltage_point_v": 25.0, "start_sell_voltage_point_v": 24.5})

    def test_bitmask_rmw_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ctrl.sqlite3")
            poller = MockPoller()
            ctrl = ControlManager(make_settings(storage.path, write_cooldown=0.0), poller, storage)
            token = ctrl.unlock()["token"]

            # Live 20142 is 35 (0b00100011): bit 0 (1), bit 1 (2), bit 5 (32) set.
            # Disable buzz_forbid (clear bit 5) and enable lcd_light_enable (set bit 6 = 64).
            # Expected: (35 & ~32) | 64 = 3 | 64 = 67. Single write to 20142!
            res = ctrl.apply(
                {"system_buzz_forbid": False, "system_lcd_light_enable": True},
                token=token,
                client_ip="127.0.0.1",
            )
            self.assertEqual(poller.writes, [(20142, 67)])
            self.assertEqual(res["written_count"], 2)
            audit = storage.list_audit()
            self.assertEqual(len(audit), 2)

            # Rollback one of the bit changes and verify it restores that bit while preserving others
            lcd_entry = next(entry for entry in audit if entry["param_key"] == "system_lcd_light_enable")
            rb = ctrl.rollback(lcd_entry["id"], token=token, client_ip="127.0.0.1")
            self.assertEqual(rb["written_count"], 1)
            self.assertEqual(poller.inverter_cfg[41], 3)

            # Preset application
            preset_res = ctrl.apply_preset("solar_first", token=token, client_ip="127.0.0.1")
            self.assertEqual(preset_res["written_count"], 2)
            self.assertEqual(poller.inverter_cfg[8], 1)
            self.assertEqual(poller.inverter_cfg[42], 0)

    def test_tier2_requires_confirm_and_cooldown_applies(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ctrl.sqlite3")
            poller = MockPoller()
            ctrl = ControlManager(make_settings(storage.path, write_cooldown=5.0), poller, storage)
            token = ctrl.unlock()["token"]

            with self.assertRaises(ControlError) as ctx:
                ctrl.apply({"float_voltage_v": 27.2}, token=token, client_ip="127.0.0.1", confirm_tier2=False)
            self.assertEqual(ctx.exception.status_code, 400)

            res = ctrl.apply({"float_voltage_v": 27.2}, token=token, client_ip="127.0.0.1", confirm_tier2=True)
            self.assertEqual(res["written_count"], 1)
            self.assertEqual(poller.charger_cfg[2], 272)

            # Immediate second write hits cooldown (429)
            with self.assertRaises(ControlError) as ctx2:
                ctrl.apply({"energy_use_mode": 1}, token=token, client_ip="127.0.0.1")
            self.assertEqual(ctx2.exception.status_code, 429)

    def test_offline_interlock_blocks_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "ctrl.sqlite3")
            poller = MockPoller(status="online")
            ctrl = ControlManager(make_settings(storage.path), poller, storage)
            token = ctrl.unlock()["token"]
            poller.status = "offline"
            with self.assertRaises(ControlError) as ctx:
                ctrl.apply({"energy_use_mode": 1}, token=token, client_ip="127.0.0.1")
            self.assertEqual(ctx.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
