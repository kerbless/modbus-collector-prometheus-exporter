#!/usr/bin/python3

import sys
import time

import yaml  # requires pyyaml
from prometheus_client import Gauge, start_http_server  # prometheus library
from pymodbus import ModbusException  # pymodbus exceptions
from pymodbus.client import ModbusSerialClient  # pymodbus client rtu (over rs485)

# Import device profile
# TODO: to script config
with open("./devices/PM3250.yaml", "r") as file:
    profile = yaml.safe_load(file)

# Defining rtu devices that will be collected and exported (SAME PROFILE)
# TODO: to script config (multi-profile)
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

# Dictionary containing all gauges used for prometheus
# Each register becomes a metric (so a Gauge)
# The naming tries to follow best practices (the "SHOULD" have a suffix describing the unit it's hard to apply here so for now it's not there).
gauges = {
    # tip: Gauge(name, description, labels)
    register["name"]: Gauge(
        f"modbus_pm3250_{register['name']}",  # note the hardcoded pm3250
        f'"{register["display_name"]}" ({register["unit"]})',
        ["modbus_device", "modbus_rs485_id"],  # TODO: dynamic labels
    )
    for register in registers.values()
}

# OpenModbusSpecs to Pymodbus unit mapping (TODO: move to file)
# https://pymodbus.readthedocs.io/en/latest/source/simulator/datamodel.html
# will use to call the pymodbus function with something like https://stackoverflow.com/questions/3061/calling-a-function-of-a-module-by-using-its-name-a-string
openModbusUnits_to_pyModbusUnits = {
    "int8": "",
    "uint8": "",
    "int16": "INT16",
    "uint16": "UINT16",
    "int32": "INT32",
    "uint32": "UINT32",
    "int64": "INT64",
    "uint64": "UINT64",
    "float32": "FLOAT32",
    "float64": "FLOAT64",
    "string": "STRING",
    "bool": "",
}

# PYMODBUS CLIENT
# https://pymodbus.readthedocs.io/en/latest/source/client.html#pymodbus.client.ModbusSerialClient

# Regarding performance:
# we are using the syncronous version of the client as in our case the transmission is the bottleneck so we don't care about the performance gain with the asyncronous client.
# https://pymodbus.readthedocs.io/en/latest/source/client.html#client-performance
# https://pymodbus.readthedocs.io/en/latest/source/client.html#serial-rs-485


pymodbus_client = ModbusSerialClient(
    # TODO to script config
    port="/tmp/ttyV1",
    baudrate=38400,
    bytesize=8,  # TODO our use case
    stopbits=1,
    parity="E",
    timeout=1,  # TODO our use case
    retries=2,  # TODO our use case
    # trace_packet – Called with bytestream received/to be sent
    # trace_pdu – Called with PDU received/to be sent
    # trace_connect – Called when connected/disconnected
)

### Calculate subgroups for bulk reads
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
    # or when max len (125) TODO check max len works as expected
    if (int(curr) + registers[curr]["length"] != int(next)) or (
        int(curr) - int(current_subset[0]) > 125
    ):
        subsets.append(current_subset)
        current_subset = []


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
                    # how many registers to read
                    reading_length = (
                        int(subset[-1])
                        - int(subset[0])
                        + int(registers[subset[-1]]["length"])
                    )

                    # The multimeter specification specifically requests using the read holding registers function (0x03) in our use case.
                    reading = pymodbus_client.read_holding_registers(
                        address=int(subset[0]),
                        count=reading_length,
                        device_id=device["rs485_id"],
                    )

                    # debug
                    print(
                        f"reading {reading_length} addresses from {subset[0]} to {subset[-1]} gave {reading.registers}"
                    )

                # bulk reading exception
                except ModbusException as exc:
                    print(f"Received ModbusException({exc}) from library")
                    pymodbus_client.close()
                    return

                # use readings
                read_up_to = 0
                for register in subset:
                    length = registers[register]["length"]

                    value = pymodbus_client.convert_from_registers(
                        reading.registers[read_up_to : read_up_to + length],
                        data_type=getattr(
                            pymodbus_client.DATATYPE,
                            openModbusUnits_to_pyModbusUnits[
                                registers[register]["type"]
                            ],
                        ),  # TODO: dynamic type (not needed for prom?)
                        word_order="big",  # TODO: confirm
                    )

                    # update gauge
                    gauge = gauges[registers[register]["name"]]
                    # labels: "modbus_device", "modbus_rtu_id" (TODO: make dynamic)
                    gauge.labels(
                        device["name"], device["rs485_id"]
                    ).set_to_current_time()
                    gauge.labels(device["name"], device["rs485_id"]).set(value)

                    # debug
                    if int(register) < 3020:
                        print(f"exported {register} with {value}")

                    read_up_to += length

        time.sleep(1)
        print("\n")

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    main()
