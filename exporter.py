#!/usr/bin/python3

# Utility imports
import random
import sys

# Import prometheus python library
from prometheus_client import Gauge, start_http_server

# Indirizzi modbus dei multimetri
rs485_device_ids = {"generale": 3, "gruppo_frigo": 4}

# Multimetri come dizionario nome - gauge
multimetri = {
    name: Gauge(f"multimetro_{name}", f"Punto misura del multimetro {name}")
    for name in rs485_device_ids
}

# Debug print
print("Exporter multimetri avviato, configurazione:\nMultimetro - id (rs485) - Gauge")
for name in rs485_device_ids:
    print(f"{name}, {rs485_device_ids[name]}, {multimetri[name]}")


# modbus reader function
def getModbusData(name):
    return random.randint(1, 10)


if __name__ == "__main__":
    # Open HTTP server with port 8400
    server, server_thread = start_http_server(8400)

    while True:
        for name in multimetri:
            multimetri[name].set_to_current_time()
            multimetri[name].set(getModbusData(name))

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    sys.exit()
