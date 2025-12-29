#!/usr/bin/env python3
import asyncio
import logging
import struct

from prometheus_client import Gauge, start_http_server
from pymodbus.client import AsyncModbusSerialClient

# ----------------------------
# Config
# ----------------------------
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 9600
PARITY = "N"
STOPBITS = 1
BYTESIZE = 8
TIMEOUT = 1.0

RS485_DEVICE_IDS = {"generale": 3, "gruppo_frigo": 4}

# Example registers (adjust to your meter)
METRIC_REGS = {
    "ingresso1_amps": {"address": 0x0000, "datatype": "float32"},
    "ingresso2_amps": {"address": 0x0002, "datatype": "float32"},
    "ingresso3_amps": {"address": 0x0004, "datatype": "float32"},
    "volts_l1_l2": {"address": 0x0006, "datatype": "float32"},
    "power_watts_total": {"address": 0x0008, "datatype": "float32"},
}

LABELS = ["multimeter", "id"]
GAUGES = {m: Gauge(f"modbus_{m}", m, LABELS) for m in METRIC_REGS}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("exporter")


# ----------------------------
# Helpers
# ----------------------------
def decode_float32(registers):
    word = (registers[0] << 16) | registers[1]
    return struct.unpack(">f", struct.pack(">I", word))[0]


async def read_metric(client, unit, cfg):
    rr = await client.read_input_registers(cfg["address"], 2, unit=unit)
    if rr.isError():
        raise Exception(rr)
    return decode_float32(rr.registers)


# ----------------------------
# Main loop
# ----------------------------
async def main():
    start_http_server(8400)
    log.info("Prometheus metrics on :8400/metrics")

    client = AsyncModbusSerialClient(
        method="rtu",
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        parity=PARITY,
        stopbits=STOPBITS,
        bytesize=BYTESIZE,
        timeout=TIMEOUT,
    )

    if not await client.connect():
        log.error("Failed to connect Modbus")
        return

    while True:
        for metric, cfg in METRIC_REGS.items():
            for name, unit in RS485_DEVICE_IDS.items():
                try:
                    val = await read_metric(client, unit, cfg)
                    GAUGES[metric].labels(name, str(unit)).set(val)
                except Exception as e:
                    log.warning(f"{name}@{unit} {metric} error: {e}")
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
