# Using a simulted modbus server: https://pymodbus.readthedocs.io/en/latest/source/server.html#pymodbus.server.ModbusSerialServer
# To understand this browse the code examples, especially from https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_sync.py
# Note that this is using pymodbus 3.x

from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartSerialServer

# 10 points per area, START FROM 1 for "Modbus standard 1-based addressing"
# for more info on what is what, check obsidian notes.
device1 = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(1, [0] * 10),
    co=ModbusSequentialDataBlock(1, [0] * 10),
    hr=ModbusSequentialDataBlock(1, [0] * 5000),
    ir=ModbusSequentialDataBlock(1, [0] * 10),
)

device2 = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(1, [0] * 10),
    co=ModbusSequentialDataBlock(1, [0] * 10),
    hr=ModbusSequentialDataBlock(1, [0] * 5000),
    ir=ModbusSequentialDataBlock(1, [0] * 10),
)

device1.setValues(3, 3001, [12])

# Map unit IDs to contexts
devices = {
    3: device1,
    4: device2,
}

context = ModbusServerContext(devices=devices, single=False)

if __name__ == "__main__":
    StartSerialServer(
        context=context,
        port="/tmp/ttyV0",  # test with: socat -d -d PTY,raw,echo=0,link=/tmp/ttyV0 PTY,raw,echo=0,link=/tmp/ttyV1
        baudrate=38400,
        bytesize=8,  # ?
        parity="E",  # even
        stopbits=1,
        timeout=1,  # ?
        # using default framer RTU
    )
