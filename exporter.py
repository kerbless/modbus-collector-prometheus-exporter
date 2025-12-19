#!/usr/bin/python3

# Utility imports
import asyncio
import random
import sys

# Import prometheus python library
from prometheus_client import Gauge, start_http_server

# Indirizzi modbus dei multimetri
rs485_device_ids = {"generale": 3, "gruppo_frigo": 4}

# Metriche esposte {nome, descrizione}
metrics = {
    "ingresso1_amps": "Line 1 current (A)",
    "ingresso2_amps": "Line 2 current (A)",
    "ingresso3_amps": "Line 3 current (A)",
    "volts_l1_l2": "Voltage L1-L2 (V)",
    "power_watts_total": "Total active power (W)",  # would best practice to export joules
}  # TODO: add all

# Labels di cui avremo delle istanze (usare entrambe non duplica i dati)
labels = ["multimeter", "id"]

# Definizione metriche prometheus, seguendo le best practices.
# (nome, descrizione, labels)
metric_gauges = {
    metric: Gauge(f"modbus_{metric}", metrics[metric], labels) for metric in metrics
}

# Inizializzazione labels (TODO: check how important it is to do this, might be better to skip it)
for gauge in metric_gauges.values():
    for name, id in rs485_device_ids.items():
        gauge.labels(name, id)

# Stampa d'inizio
print("Exporter multimetri avviato, inizio raccolta per le seguenti metriche:")
for metric in metric_gauges:
    print(metric)


# TODO: modbus reader function (use library?)
async def getModbusData(metric, id):
    return random.randint(1, 10)


async def main():
    # Open HTTP server with port 8400
    server, server_thread = start_http_server(8400)

    while True:
        for metric, gauge in metric_gauges.items():
            for name, id in rs485_device_ids.items():
                updateValue = await getModbusData(metric, id)

                # gauge.labels(name, id).set_to_current_time() # TODO: confirm that this is done automatically when .set
                gauge.labels(name, id).set(updateValue)

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())
