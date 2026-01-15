#!/usr/bin/python3

# Utility imports
import json
import random
import sys

from prometheus_client import Gauge, start_http_server

# Import modbus and prometheus libraries
from pymodbus.client import ModbusSerialClient

# Indirizzi modbus dei multimetri
rs485_device_ids = {"generale": 3, "gruppo_frigo": 4}

# Creazione client pymodbus per ciascun multimetro
pymodbus_clients = {}
for multimeter in rs485_device_ids:
    # https://pymodbus.readthedocs.io/en/latest/source/client.html#pymodbus.client.ModbusSerialClient
    pymodbus_clients[multimeter] = ModbusClient.ModbusSerialClient(
        "/dev/ttyUSB0",  # port
        # timeout=10,
        # retries=3,
        baudrate=38400,
        bytesize=8,
        parity="E",  # parity: even
        stopbits=1,
        # handle_local_echo=False,
    )

# Metriche da leggere da json
with open("PM3200_modbus_metrics_AI.json", "r") as file:
    metrics = json.load(file)

print(metrics)

# Labels di cui avremo delle istanze (usare entrambe non duplica i dati, le coppie sono uniche)
labels = ["multimeter", "id"]

# Definizione metriche prometheus, seguendo le best practices.
# (nome, descrizione, labels)
metric_gauges = {
    metric: Gauge(f"modbus_{metric}", metrics[metric], labels) for metric in metrics
}

# Inizializzazione labels (TODO: check how important it is to do this, might be able to skip it)
for gauge in metric_gauges.values():
    for name, id in rs485_device_ids.items():
        gauge.labels(name, id)

# Stampa d'inizio
print("Exporter multimetri avviato, inizio raccolta per le seguenti metriche:")
for metric in metric_gauges:
    print(metric)

# pymodbus client

# Read https://pymodbus.readthedocs.io/en/latest/source/client.html#client-performance
# We are using the syncronous function as in our case
# the bottleneck is on the transmission so we don't care about
# asyncronous performance right now
# Read https://pymodbus.readthedocs.io/en/latest/source/client.html#serial-rs-485

pymodbus_client = ModbusSerialClient(
    port="/tmp/ttyV1",
    baudrate=38400,
)


def getModbusData(metric, id):
    print(pymodbus_client.read_holding_registers(1, 5, unit=1))


def main():
    # connect to pymodbus client
    pymodbus_client.connect()

    # Open HTTP server with port 8400 for prometheus to scrape
    server, server_thread = start_http_server(8400)

    while True:
        for metric, gauge in metric_gauges.items():
            for name, id in rs485_device_ids.items():
                updateValue = client.read_holding_registers(248, 4, unit=1)

                # gauge.labels(name, id).set_to_current_time() # TODO: confirm that this is done automatically when .set
                gauge.labels(name, id).set(updateValue)

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    pymodbus_client.close()
    sys.exit()


if __name__ == "__main__":
    pass
