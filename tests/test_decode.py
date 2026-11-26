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

    def test_pv1800_accumulated_counters_use_decimal_words(self):
        charger = [0] * 21
        charger[16] = 2
        charger[17] = 3456
        charger[18] = 7
        charger[19] = 8
        charger[20] = 9
        inverter = [0] * 79
        inverter[44] = 1
        inverter[45] = 2345
        inverter[46] = 0
        inverter[47] = 5104
        inverter[52] = 1
        inverter[53] = 6975

        snapshot = decode_snapshot(
            sections={"charger_status": charger, "inverter_status": inverter},
            captured_at="2026-09-11T12:00:00Z",
            source={"port": "test", "slave_id": 4, "baudrate": 19200},
            errors={},
            latency_ms=1.0,
        )

        self.assertEqual(snapshot["status"]["charger"]["accumulated_power_wh"], 2_345_600.0)
        self.assertEqual(snapshot["status"]["charger"]["accumulated_time"], "07:08:09")
        self.assertEqual(snapshot["status"]["inverter"]["accumulated_charger_power_wh"], 1_234_500.0)
        self.assertEqual(snapshot["status"]["inverter"]["accumulated_discharger_power_wh"], 510_400.0)
        self.assertEqual(snapshot["status"]["inverter"]["accumulated_load_power_wh"], 1_697_500.0)

    def test_v030_decodes_flags_enums_and_autonomy(self):
        charger = [0] * 21
        charger[4] = 0
        charger[5] = 265
        charger[12] = 32  # bit 5: pv_voltage_low

        inverter = [0] * 79
        inverter[4] = 265
        inverter[6] = 0
        inverter[14] = 240
        inverter[72] = 300
        inverter[74] = 24

        charger_cfg = [0] * 24
        charger_cfg[2] = 270
        charger_cfg[9] = 1
        charger_cfg[10] = 200

        inverter_cfg = [0] * 44
        inverter_cfg[8] = 3
        inverter_cfg[10] = 1
        inverter_cfg[26] = 240
        inverter_cfg[41] = 35  # 0b00100011
        inverter_cfg[42] = 2

        snapshot = decode_snapshot(
            sections={
                "charger_status": charger,
                "inverter_status": inverter,
                "charger_config": charger_cfg,
                "inverter_config": inverter_cfg,
            },
            captured_at="2026-11-26T14:00:00Z",
            source={"port": "test", "slave_id": 4, "baudrate": 19200},
            errors={},
            latency_ms=10.0,
        )

        chg_flags = snapshot["status"]["charger"]["error_flags"]
        self.assertEqual(len(chg_flags), 1)
        self.assertEqual(chg_flags[0]["code"], "pv_voltage_low")
        self.assertEqual(chg_flags[0]["severity"], "info")

        inv_cfg = snapshot["configuration"]["inverter"]
        self.assertEqual(inv_cfg["energy_use_mode_label"], "UTI")
        self.assertEqual(inv_cfg["grid_protect_standard_label"], "UPS")
        self.assertEqual(inv_cfg["charger_source_priority_label"], "SNU")
        self.assertTrue(inv_cfg["system_setting_flags"]["overload_restart_forbid"])
        self.assertTrue(inv_cfg["system_setting_flags"]["overtemp_restart_forbid"])
        self.assertTrue(inv_cfg["system_setting_flags"]["buzz_forbid"])
        self.assertFalse(inv_cfg["system_setting_flags"]["lcd_light_enable"])

        autonomy = snapshot["autonomy"]
        self.assertTrue(autonomy["discharging"])
        self.assertIsNotNone(autonomy["estimated_minutes"])
        self.assertGreater(autonomy["estimated_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
