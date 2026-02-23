#!/usr/bin/python3

# Utility imports
import glob
import json
import os
import sys
import time

import yaml  # requires pyyaml

# Import modbus and prometheus libraries
from prometheus_client import Gauge, start_http_server
from pymodbus import ModbusException
from pymodbus.client import ModbusSerialClient

# Multimeter modbus addresses (TODO moving to yaml)
# rs485_device_ids = {"generale": 3, "gruppo_frigo": 4}

# Import devices information
devices_dir = "./devices/"
devices = {}
for filepath in glob.glob(os.path.join(devices_dir, "*.yaml")):
    with open(filepath, "r") as file:
        filename = os.path.splitext(os.path.basename(filepath))[0]
        devices[filename] = yaml.safe_load(file)

# BRIDGE device information to prometheus metric definition following best practices.

# Labels of which we will have instances (using both does not duplicate data as each couple is unique)
labels = ["multimeter", "unit_id"]
Gauge(f"modbus_{device}", description, labels)

gauges = {}
for device, device_data in devices.items():

# Metrics definition - tip: Gauge(name, description, labels)
metric_gauges = {
    metric["name"]: Gauge(f"modbus_{metric['name']}", metric["description"], labels) for metric in metrics
}

# Label initialization (TODO: can be skipped right?)
# for gauge in metric_gauges.values():
#     for name, id in rs485_device_ids.items():
#         gauge.labels(name, id)

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

# Starting print.
print("Exporter multimetri avviato, inizio raccolta per le seguenti metriche:")
for metric in metric_gauges:
    print(metric)


def main():
    # connect to pymodbus client
    pymodbus_client.connect()

    # Open HTTP server with port 8400 for prometheus to scrape
    server, server_thread = start_http_server(8400)

    while True:
        for metric in metrics:
            for name, id in rs485_device_ids.items():
                try:
                    reading = pymodbus_client.read_holding_registers(
                        address=int(metric["address"]),
                        count=2,  # ?!
                        device_id=id,
                    )

                except ModbusException as exc:  # pragma: no cover
                    print(f"Received ModbusException({exc}) from library")
                    pymodbus_client.close()
                    return

                value_int32 = pymodbus_client.convert_from_registers(
                    reading.registers,
                    data_type=pymodbus_client.DATATYPE.INT32,
                    word_order="big",
                )

                print(
                    f"reading {metric['name']} from device {name} got {value_int32} {type(value_int32)}"
                )
                # gauge.labels(name, id).set_to_current_time() # TODO: confirm that this is done automatically when .set
                metric_gauges[metric["name"]].labels(name, id).set(
                    value_int32
                )  # TODO: WHY TYPE??
        time.sleep(1)
        print("\n")

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    main()
