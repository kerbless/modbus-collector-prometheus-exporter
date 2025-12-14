#!/usr/bin/python3

# Utility imports
import subprocess
import sys

# Import prometheus python library
from prometheus_client import Gauge, start_http_server

# indirizzi modbus dei multimetri
rs485_device_ids = {"generale": 3, "gruppo_frigo": 4}


# modbus reader function
def getModbusData(id_device):
    template_command = f"modbus -s {id_device} -b 38400 -P e -p 1 -r registers.modbus /dev/ttyUSB0 \*"  # TODO: ask for output of THIS command
    output = subprocess.run(template_command, shell=True, capture_output=True).stdout
    return output.decode("utf-8").split("\n")[1:]


if __name__ == "__main__":
    # Open HTTP server with port 8000
    server, server_thread = start_http_server(8000)

    # Create Gauge element for each device id
    multimeters_gauge = {"generale": object, "gruppo_frigo": object}
    for el in rs485_device_ids:
        multimeters_gauge[el] = Gauge(
            f"multimetro-{el}", f"Punto misura del multimetro {el}"
        )

    #
    for line in get:
        try:
            lab, val = line.split(":")
            print(f'multimetri-{lab}{{punto_misura="{el}"}} = {float(val):.2f}')
        except:
            pass

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    sys.exit()
