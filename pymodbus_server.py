# Using a simulted modbus server: https://pymodbus.readthedocs.io/en/latest/source/server.html#pymodbus.server.ModbusSerialServer
# To understand this browse the code examples, especially from https://github.com/pymodbus-dev/pymodbus/blob/dev/examples/server_sync.py

from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import ModbusSerialServer

# Create a datastore (holding registers, coils, etc.)
store = ModbusSlaveContext(di=dict(), co=dict(), hr=dict(), ir=dict())
context = ModbusServerContext(slaves=store, single=True)

# Device identification (optional)
identity = ModbusDeviceIdentification()
identity.VendorName = "MyVendor"
identity.ProductCode = "MyProduct"
identity.VendorUrl = "http://example.com"
identity.ProductName = "Modbus RTU Server"
identity.ModelName = "RTU Model"
identity.MajorMinorRevision = "1.0"

# Start the Modbus RTU server
server = ModbusSerialServer(
    context,
    framer="rtu",
    port="/dev/ttyUSB0",  # Replace with your serial port
    baudrate=9600,
    identity=identity,
)

if __name__ == "__main__":
    print("Starting Modbus RTU Server...")
    server.serve_forever()
