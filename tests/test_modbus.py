import unittest

from must_dashboard.config import Settings
from must_dashboard.modbus import ModbusError, ModbusRTU, crc16


class FakeSerial:
    def __init__(self, responses, **_kwargs):
        self.responses = responses
        self.buffer = bytearray()
        self.is_open = True
        self.writes = []
        self.rts = None
        self.dtr = None

    def reset_input_buffer(self):
        self.buffer.clear()

    def write(self, data):
        self.writes.append(data)
        function = data[1]
        if function == 0x03:
            start = int.from_bytes(data[2:4], "big")
            count = int.from_bytes(data[4:6], "big")
            reply = self.responses[(start, count)]
        elif function == 0x06:
            addr = int.from_bytes(data[2:4], "big")
            val = int.from_bytes(data[4:6], "big")
            reply = self.responses[(0x06, addr, val)]
            if callable(reply):
                reply = reply(addr, val)
        else:
            raise AssertionError(f"unexpected function {function}")
        self.buffer.extend(reply)
        return len(data)

    def flush(self):
        pass

    def read(self, size=1):
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result

    def close(self):
        self.is_open = False


def response(slave_id, registers):
    body = bytes((slave_id, 3, len(registers) * 2))
    payload = b"".join(value.to_bytes(2, "big") for value in registers)
    return body + payload + crc16(body + payload)


def write_single_response(slave_id, address, value):
    body = bytes((slave_id, 0x06, address >> 8, address & 0xFF, value >> 8, value & 0xFF))
    return body + crc16(body)


def exception_response(slave_id, function, code):
    body = bytes((slave_id, function | 0x80, code))
    return body + crc16(body)


def settings():
    return Settings(
        base_dir=None,
        public_dir=None,
        db_path=None,
        host="127.0.0.1",
        port=8090,
        serial_port="fake",
        slave_id=4,
        baudrate=19200,
        poll_interval=15,
        sample_interval=60,
        config_interval=300,
        serial_timeout=0.2,
        inter_request_delay=0,
        retention_days=730,
    )


class ModbusTests(unittest.TestCase):
    def test_read_holding_registers_validates_frame(self):
        fake = FakeSerial({(25201, 2): response(4, [0x1234, 0xFFF0])})
        client = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake)
        self.assertEqual(client.read_holding(25201, 2), [0x1234, 0xFFF0])
        self.assertEqual(fake.writes[0], bytes.fromhex("04 03 62 71 00 02 8b fd"))

    def test_bad_crc_is_rejected(self):
        frame = bytearray(response(4, [1]))
        frame[-1] ^= 0xFF
        fake = FakeSerial({(25201, 1): bytes(frame)})
        client = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake)
        with self.assertRaisesRegex(ModbusError, "CRC"):
            client.read_holding(25201, 1)

    def test_device_exception_is_reported(self):
        fake = FakeSerial({(25201, 1): exception_response(4, 3, 2)})
        client = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake)
        with self.assertRaisesRegex(ModbusError, "exception code: 2"):
            client.read_holding(25201, 1)

    def test_write_single_register_skips_noop(self):
        fake = FakeSerial({(20109, 1): response(4, [3])})
        client = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake)
        result = client.write_single_register(20109, 3)
        self.assertEqual(result["status"], "noop")
        self.assertFalse(result["written"])
        self.assertEqual(len(fake.writes), 1)

    def test_write_single_register_writes_and_verifies(self):
        register_state = {"val": 3}

        def handle_write(addr, val):
            register_state["val"] = val
            return write_single_response(4, addr, val)

        class DynamicFakeSerial(FakeSerial):
            def write(self, data):
                self.writes.append(data)
                if data[1] == 0x03:
                    self.buffer.extend(response(4, [register_state["val"]]))
                elif data[1] == 0x06:
                    addr = int.from_bytes(data[2:4], "big")
                    val = int.from_bytes(data[4:6], "big")
                    self.buffer.extend(handle_write(addr, val))
                return len(data)

        fake = DynamicFakeSerial({})
        client = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake)
        result = client.write_single_register(20109, 1, verify=True)
        self.assertEqual(result["status"], "verified")
        self.assertTrue(result["written"])
        self.assertEqual(result["before"], 3)
        self.assertEqual(result["after"], 1)
        self.assertEqual(len(fake.writes), 3)
        self.assertEqual(fake.writes[1][:6], bytes.fromhex("04 06 4e 8d 00 01"))

    def test_write_single_register_rejects_bad_crc_and_exception(self):
        bad_echo = bytearray(write_single_response(4, 20109, 1))
        bad_echo[-1] ^= 0xFF
        fake_crc = FakeSerial({
            (20109, 1): response(4, [3]),
            (0x06, 20109, 1): bytes(bad_echo),
        })
        client_crc = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake_crc)
        with self.assertRaisesRegex(ModbusError, "CRC"):
            client_crc.write_single_register(20109, 1)

        fake_exc = FakeSerial({
            (20109, 1): response(4, [3]),
            (0x06, 20109, 1): exception_response(4, 6, 3),
        })
        client_exc = ModbusRTU(settings(), serial_factory=lambda *args, **kwargs: fake_exc)
        with self.assertRaisesRegex(ModbusError, "exception code: 3"):
            client_exc.write_single_register(20109, 1)


if __name__ == "__main__":
    unittest.main()
