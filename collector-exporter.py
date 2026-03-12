#!/usr/bin/python3

import re
import sys
import time

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

# Dictionary containing all gauges (register = metric) used for prometheus
gauges = {
    # tip: Gauge(name, description, labels)
    register["name"]: Gauge(
        register["name"],
        f'"{register["display_name"]}" ({register["unit"]})',
        ["modbus_device", "modbus_rs485_id"],  # TODO: make dynamic labels
    )
    for register in profile["registers"].values()
}

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
registers = profile["registers"]
addresses = sorted(registers.keys())

print(registers[addresses[0]]["name"])

# detect next continuous block to read
subsets = []
current_subset = []

# for each register address index
for i in range(0, len(addresses) - 1):
    curr = addresses[i]
    next = addresses[i + 1]
    current_subset.append(curr)

    # if CONTIGUOUS, i.e. curr address + curr length = next address
    if int(curr) + registers[curr]["length"] == int(next):
        continue
    else:
        subsets.append(current_subset)
        current_subset = []
        continue

print(subsets)


def main():
    # connect to pymodbus client
    pymodbus_client.connect()

    # Open HTTP server with port 8400 for prometheus to scrape
    server, server_thread = start_http_server(8400)

    # Continuously reading/exporting each register metrics
    while True:
        for device in devices:
            while next_reg_index < len(registers) and block_length < 125:
                reg_index = next_reg_index
                num_reg = 1  # number of register will be read
                tot_len = registers[register_keys[reg_index]]["length"]  # total lenght

                for i in range(
                    reg_index, len(register_keys)
                ):  # for each subsequent register starting from current one
                    print(
                        f"testing {(registers[register_keys[i]]['length'] + int(register_keys[i]))} == {int(register_keys[i + 1])}"
                    )
                    if (
                        # i.e. if CONTIGUOUS
                        # if the current register address + its lenght
                        # == next register
                        (registers[register_keys[i]]["length"] + int(register_keys[i]))
                        == int(register_keys[i + 1])
                    ):
                        tot_len += registers[register_keys[i + 1]]["length"]
                        num_reg = num_reg + 1
                    else:
                        next_reg_index = i + 1
                        break
                print(
                    f"reading register {register_keys[reg_index]} for {num_reg} registers with a total lenght of {tot_len}, will continue from {register_keys[next_reg_index]}\n"
                )

                # bulk read
                try:
                    # The multimeter specification specifically requests using the read holding registers function (0x03) in our use case.
                    reading = pymodbus_client.read_holding_registers(
                        address=int(registers[reg_index]),
                        count=tot_len,
                        device_id=device["rs485_id"],
                    )

                except ModbusException as exc:
                    print(f"Received ModbusException({exc}) from library")
                    pymodbus_client.close()
                    return

                print(reading)
                # update
                # convert raw value to type (TODO: make dynamic with profile)
                # value = pymodbus_client.convert_from_registers(
                #     reading.registers,
                #     data_type=pymodbus_client.DATATYPE.INT32,  # here I need to map yaml data to pymodbus
                #     word_order="big",
                # )

                # print(
                #     f"reading {register['name']} from device {device['name']} got {value} {type(value)}"
                # )

                # gauge.labels(name, id).set_to_current_time() # TODO: confirm that this is done automatically when .set

                # labels: "modbus_device", "modbus_rtu_id" (TODO: make dynamic)
                # gauges[device["name"]].labels(device["name"], device["rs485_id"]).set(
                #     value
                # )
        time.sleep(1)
        print("\n")

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    main()
