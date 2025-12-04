#!/usr/bin/python3

# Utility imports
import sys

# Import prometheus python library
from prometheus_client import Gauge, start_http_server

if __name__ == "__main__":
    # Open HTTP server with port 8000
    server, server_thread = start_http_server(8000)

    # Create Gauge element
    for el in rs485_device_ids:
        multimeters_gauge = Gauge(f"punto_misura-{el}", "Description of gauge")

    # Generate some requests.
    while True:
        lab = "lab?"
        el = 2
        val = 1293842
        print(f'multimetri-{lab}{{punto_misura="{el}"}} = {float(val):.2f}')

    # Graceful exit (just to practice)
    server.shutdown()
    server_thread.join()  # wait for a thread to finish and exit
    sys.exit()
