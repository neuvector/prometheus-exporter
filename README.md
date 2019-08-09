# Prometheus exporter and Grafana template

![](nv_grafana.png)

### NV_Exporter Setup:

- Clone the repository
- Make sure you installed Python 3 and python3-pip:
```
$ sudo apt-get install python3
$ sudo apt-get install python3-pip
```
- Install the Prometheus Python client:
```
$ sudo pip install -U setuptools
$ sudo pip install -U pip
$ sudo pip3 install prometheus_client requests
```

- Modify docker-compose.yml or nv_exporter.yml. Specify NeuVector controller's RESTful API endpoint, login username and password and the port that the export listens on through environment variables. **It's highly recommanded to create a read-only user account for the exporter.**
- Start NeuVector exporter container.
- Open browser, go to: [exporter_host]:[exporter_port] (example: 10.1.22.11:8068)
- If you can load the metric page, the exporter is working fine.

### Prometheus Setup:

- Add exporter target in your prometheus.yml file under `scrape_configs`:
```
global:
  evaluation_interval: 10s

scrape_configs:
  - job_name: prometheus
    scrape_interval: 10s
    static_configs:
      - targets: ["localhost:9090"]
  - job_name: nv-exporter
    scrape_interval: 30s
    static_configs:
      - targets: targets: ["neuvector-svc-prometheus-exporter.neuvector:8068"]
```

- Start Prometheus container. "docker run" example,
```
docker run -itd -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml --name prom prom/prometheus
```
- After deployed Prometheus, open browser and go to: prometheus_host:9090 (example: localhost:9090)
- On the top bar go to `Status -> Targets` to check exporter status. If the name is blue and `State` is `UP`, the exporter is running and Prometheus is successfully connected to the exporter.
- On the top bar go to `Graph` and in the `Expression` box type `nv` to view all the metrics the exporter has.

### Grafana Setup:
- Start Grafana container. "docker run" example,
```
docker run -d -p 3000:3000 --name grafana grafana/grafana
```
- After deployed Grafana, open browser and go to: grafana_host:3000 (example: localhost:3000)
- Login and add Prometheus source, find the `+` on the left bar, select `Import`
- Upload NeuVector dashboard templet JSON file.
