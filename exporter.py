#!/usr/bin/python3

# Utility imports
import glob
import json
import os
import sys
import time
from pdb import pm

import yaml  # requires pyyaml
from prometheus_client import Gauge, start_http_server  # prometheus library
from pymodbus import ModbusException  # pymodbus exceptions
from pymodbus.client import ModbusSerialClient  # pymodbus client rtu (over rs485)

# Import device profile
with open("./devices/PM3250.yaml", "r") as file:
    pm3250 = yaml.safe_load(file)

# Modbus rtu devices
devices = [
    {
        "name": "modbus_power_meter_general",
        "description": "multimetro generale",
        "registers": pm3250["registers"],
        "rs485_id": 3,
    },
    {
        "name": "modbus_power_meter_cooling",
        "description": "multimetro gruppo frigo",
        "registers": pm3250["registers"],  # no dup data right?
        "rs485_id": 4,
    },
]

# Dictionary containing all gauges (one per register) for the given device
# tip: Gauge(name, description, labels)

gauges = {
    device["name"]: Gauge(
        device["name"],
        device["description"],
        ["modbus_device", "modbus_rs485_id"],
    )
    for device in devices
}

# Starting print.
print("Exporter multimetri avviato, inizio raccolta per le seguenti metriche:")
for device in devices:
    for register, register_profile in device["registers"].items():
        print(f"Device {device['name']}: {register_profile['name']} (addr: {register})")


# PYMODBUS CLIENT
# https://pymodbus.readthedocs.io/en/latest/source/client.html#pymodbus.client.ModbusSerialClient

# Regarding performance:
# we are using the syncronous version of the client as in our case the transmission is the bottleneck so we don't care about the performance gain with the asyncronous client.
# https://pymodbus.readthedocs.io/en/latest/source/client.html#client-performance
# https://pymodbus.readthedocs.io/en/latest/source/client.html#serial-rs-485

pymodbus_client = ModbusSerialClient(
    port="/tmp/ttyV1",
    baudrate=38400,
    bytesize=8,  # how much for our multimeters?
    stopbits=1,
    parity="E",
    timeout=1,  # ?
    retries=1,  #!?
    # trace_packet – Called with bytestream received/to be sent
    # trace_pdu – Called with PDU received/to be sent
    # trace_connect – Called when connected/disconnected
)


def main():
    # connect to pymodbus client
    pymodbus_client.connect()

    # Open HTTP server with port 8400 for prometheus to scrape
    server, server_thread = start_http_server(8400)

    while True:
        for device in devices:
            for register, register_profile in device["registers"].items():
                try:
                    reading = pymodbus_client.read_holding_registers(
                        address=int(register),
                        count=register_profile["length"],  # ?!
                        device_id=device["rs485_id"],
                    )

                except ModbusException as exc:  # pragma: no cover
                    print(f"Received ModbusException({exc}) from library")
                    pymodbus_client.close()
                    return

                value = pymodbus_client.convert_from_registers(
                    reading.registers,
                    data_type=pymodbus_client.DATATYPE.INT32,  # here I need to map yaml data to pymodbus
                    word_order="big",
                )

                print(
                    f"reading {register_profile['name']} from device {device['name']} got {value} {type(value)}"
                )

                # gauge.labels(name, id).set_to_current_time() # TODO: confirm that this is done automatically when .set
                # labels: "modbus_device", "modbus_rtu_id"
                gauges[device["name"]].labels(device["name"], device["rs485_id"]).set(
                    value
                )
        time.sleep(1)
        print("\n")

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    main()
