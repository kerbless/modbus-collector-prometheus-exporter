#!/usr/bin/python3

import re
import sys
import time
from posix import read

import yaml  # requires pyyaml
from prometheus_client import Gauge, start_http_server  # prometheus library
from pymodbus import ModbusException  # pymodbus exceptions
from pymodbus.client import ModbusSerialClient  # pymodbus client rtu (over rs485)

# Import device profile
with open("./devices/PM3250.yaml", "r") as file:
    profile = yaml.safe_load(file)

# Defining rtu devices that will be collected and exported (SAME PROFILE)
devices = [
    {
        "name": "modbus_power_meter_general",
        "description": "multimetro generale",
        "rs485_id": 3,
    },
    {
        "name": "modbus_power_meter_cooling",
        "description": "multimetro gruppo frigo",
        "rs485_id": 4,
    },
]

registers = profile["registers"]  # TODO filter needed ones and e.g. only float32

# Dictionary containing all gauges (register = metric) used for prometheus
gauges = {
    # tip: Gauge(name, description, labels)
    register["name"]: Gauge(
        register["name"],
        f'"{register["display_name"]}" ({register["unit"]})',
        ["modbus_device", "modbus_rs485_id"],  # TODO: make dynamic labels
    )
    for register in registers.values()
}

for gauge in gauges:
    print(f"created gauge {gauge}")

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

# Calculate subgroups for bulk reads
# get registers and their keys ordered
addresses = sorted(registers.keys())

# detect next continuous block to read
subsets = []
current_subset = []

# for each register address index
for i in range(0, len(addresses) - 1):
    curr = addresses[i]
    next = addresses[i + 1]
    current_subset.append(curr)

    # split when NOT CONTIGUOUS, i.e. curr address + curr length != next address
    # or when max len (125)
    if (int(curr) + registers[curr]["length"] != int(next)) or (
        int(curr) - int(current_subset[0]) > 125
    ):
        subsets.append(current_subset)
        current_subset = []

print(subsets)


def main():
    # connect to pymodbus client
    pymodbus_client.connect()

    # Open HTTP server with port 8400 for prometheus to scrape
    server, server_thread = start_http_server(8400)

    # Continuously reading/exporting each register metrics
    while True:
        for device in devices:
            for subset in subsets:
                # bulk read
                try:
                    # The multimeter specification specifically requests using the read holding registers function (0x03) in our use case.

                    # reading length for bulk read or single register
                    reading_length = max(
                        int(subset[-1]) - int(subset[0]),
                        int(registers[subset[0]]["length"]),
                    )

                    reading = pymodbus_client.read_holding_registers(
                        address=int(subset[0]),
                        count=reading_length,
                        device_id=device["rs485_id"],
                    )

                except ModbusException as exc:
                    print(f"Received ModbusException({exc}) from library")
                    pymodbus_client.close()
                    return

                print(subset)
                print(reading.registers)

                read_up_to = 0
                for register in subset:
                    length = registers[register]["length"]
                    print(openModbusUnits_to_pyModbusUnits[registers[register]["type"]])
                    value = pymodbus_client.convert_from_registers(
                        reading.registers[read_up_to : read_up_to + length],
                        data_type=getattr(
                            pymodbus_client.DATATYPE,
                            openModbusUnits_to_pyModbusUnits[
                                registers[register]["type"]
                            ],
                        ),  # here I need to map yaml data to pymodbus
                        word_order="big",
                    )
                    print(value)

                    gauge = gauges[registers[register]["name"]]
                    # check if set_to_current_time() happens automatically if there is something weird here with the time
                    gauge.labels()
                    # labels: "modbus_device", "modbus_rtu_id" (TODO: make dynamic)
                    gauges[register].labels(device["name"], device["rs485_id"]).set(
                        value
                    )

                    read_up_to += length

                quit()

        time.sleep(1)
        print("\n")

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    main()
