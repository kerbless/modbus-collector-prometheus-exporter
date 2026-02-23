# Progetto di ingegneria informatica

> Progetto svolto da Burroni Blu sotto la supervisione del prof. Barenghi Alessandro, Politecnico di Milano A.A. 2025/2026.

Sviluppo di un prometheus exporter in python (usando la [libreria ufficiale di prometheus](https://prometheus.github.io/client_python/) e quella [pymodbus](https://pymodbus.readthedocs.io), seguendo le [best practices](https://prometheus.io/docs/practices/naming/)) per estrarre metriche dai multimetri della sala macchine del deib in modo da calcolarne il PUE e integrarlo nello stack di monitoring.

## Develop and test

`uv sync`

`socat -d -d PTY,raw,echo=0,link=/tmp/ttyV0 PTY,raw,echo=0,link=/tmp/ttyV1`

`uv run pymodbus_server.py`

`uv run exporter.py`
