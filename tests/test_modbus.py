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
        start = int.from_bytes(data[2:4], "big")
        count = int.from_bytes(data[4:6], "big")
        self.buffer.extend(self.responses[(start, count)])
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


if __name__ == "__main__":
    unittest.main()
