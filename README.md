# Progetto di ingegneria informatica

> Progetto svolto da Burroni Blu sotto la supervisione del prof. Barenghi Alessandro, Politecnico di Milano A.A. 2025/2026.

Sviluppo di un exporter Prometheus in Python (usando la [libreria ufficiale di prometheus](https://prometheus.github.io/client_python/) e quella [pymodbus](https://pymodbus.readthedocs.io), seguendo le [best practices](https://prometheus.io/docs/practices/naming/)) per estrarre metriche tramite Modbus dai multimetri della sala macchine del DEIB in modo da calcolarne il PUE e integrarlo nello stack di monitoring tramite una dashboard su Grafana.

## Configurazione ambiente e test

Per ricreare l'ambiente del progetto e testarlo:
1. Verifica di aver installato git, python e pip/uv.
2. Clona il repository.
3. Dalla directory del repository esegui `uv sync` o `pip install -r requirements.txt` per configurare l'ambiente virtuale di Python (se utilizzi pip assicurati di averlo creato/attivato).
4. Se necessario, installa ed esegui `socat -d -d PTY,raw,echo=0,link=/tmp/ttyV0 PTY,raw,echo=0,link=/tmp/ttyV1` per simulare la connessione modbus.
5. Se necessario, esegui il server che simula i dispositivi modbus con `uv run pymodbus_server.py`.
6. Se necessario, verifica che il profilo del dispositivo sia conforme alle specifiche OpenModbusSpecs seguendo le istruzioni da https://github.com/stekker/OpenModbusSpecs/tree/main.
7. Esegui l'exporter con `uv run exporter.py` e leggi l'output o le metriche esposte su localhost:8400 (vedi example_prometheus.yaml)
