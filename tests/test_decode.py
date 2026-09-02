import unittest

from must_dashboard.decode import decode_snapshot, signed16, version


class DecodeTests(unittest.TestCase):
    def test_signed16_and_version(self):
        self.assertEqual(signed16(0xFFF0), -16)
        self.assertEqual(version([22534], 0), "2.25.34")

    def test_snapshot_exposes_known_metrics_and_raw_sections(self):
        identity = [0] * 16
        identity[0] = 1800
        identity[1] = 0xFFFF
        identity[2] = 0xFFFF
        identity[3] = 10101
        identity[4] = 22534
        charger = [0] * 21
        charger[4] = 280
        charger[5] = 268
        charger[6] = 12
        charger[7] = 250
        inverter = [0] * 79
        inverter[2] = 3200
        inverter[4] = 268
        inverter[5] = 2297
        inverter[6] = 2306
        inverter[12] = 22
        inverter[13] = 380
        inverter[14] = 361
        inverter[15] = 16
        inverter[24] = 4995
        inverter[25] = 4995
        inverter[70] = 10101
        inverter[71] = 22534
        inverter[76] = 3200
        inverter[77] = 10414

        snapshot = decode_snapshot(
            sections={"identity": identity, "charger_status": charger, "inverter_status": inverter},
            captured_at="2026-09-02T12:00:00Z",
            source={"port": "test", "slave_id": 4, "baudrate": 19200},
            errors={},
            latency_ms=123.4,
        )
        self.assertEqual(snapshot["identity"]["model"], "PV1800")
        self.assertEqual(snapshot["metrics"]["rated_power_w"], 3200)
        self.assertEqual(snapshot["metrics"]["load_power_w"], 361)
        self.assertEqual(snapshot["metrics"]["grid_voltage_v"], 230.6)
        self.assertEqual(snapshot["metrics"]["grid_frequency_hz"], 49.95)
        self.assertEqual(snapshot["raw"]["inverter_status"], inverter)


if __name__ == "__main__":
    unittest.main()
