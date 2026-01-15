# Using a simulted modbus server: https://pymodbus.readthedocs.io/en/latest/source/server.html#pymodbus.server.ModbusSerialServer
# To understand this browse the code examples, especially from https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_sync.py
# Note that this is using pymodbus 3.x

from pymodbus import FramerType
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server import StartSerialServer

# 100 points per area, START FROM 1 for "Modbus standard 1-based addressing"
# for more info on what is what, check obsidian notes.
di = ModbusSequentialDataBlock(1, [0] * 100)
co = ModbusSequentialDataBlock(1, [0] * 100)
hr = ModbusSequentialDataBlock(1, [0] * 100)
ir = ModbusSequentialDataBlock(1, [0] * 100)

device = ModbusDeviceContext(di=di, co=co, hr=hr, ir=ir)
context = ModbusServerContext(devices=device, single=True)  # device-id default is 1

if __name__ == "__main__":
    StartSerialServer(
        context=context,
        port="/tmp/ttyV0",  # for testing: socat -d -d PTY,raw,echo=0,link=/tmp/ttyV0 PTY,raw,echo=0,link=/tmp/ttyV1
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=1,
        framer=FramerType.RTU,  # is default anyways
    )
