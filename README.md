NeuVector Exporter

##	1st NV_Exporter Setup:

####		1. Download nv_exporter.py

####		2. Make sure you installed Python 3

####		3. Install the Prometheus Python client:
			$ sudo pip install -U setuptools
			$ sudo pip install -U pip
			$ sudo pip install prometheus_client requests

####		4. Run exporter:
			$ python3 nv_exporter.py -p [Exporter_Port] -s [API_Host:API_Port]
			(example: $ python3 nv_exporter.py -p 1234 -s 10.1.22.11:30443, for more API targets: $ python3 nv_exporter.py -p 1234 -s 10.1.22.11:30443 -s 10.1.22.12:34567)

####		5.	Open browser, go to: 
			[Exporter_Host]:[Exporter_Port] (example: 10.1.22.11:1234)

####		6.	If you can load the metric page, the exporter is working fine.




##	2nd Prometheus Setup:

####		1. Add exporter target in your prometheus.yml file under `scrape_configs`:
			global:
			  evaluation_interval: 10s

			scrape_configs:
			  - job_name: prometheus
			    scrape_interval: 10s
			    static_configs:
			      - targets: ["localhost:9090"]
#### 	add:
			  - job_name: nv-exporter
			    scrape_interval: 30s
			    static_configs:
			      - targets: ["[Exporter_Host]:[Exporter_Port]"]
			      (example: - targets: ["10.1.22.11:1234"])

####		2. You can also change the scrape interval

####		3. After deployed Prometheus, open browser and go to:
			Prometheus_Host:9090 (example: localhost:9090)

####		4. On the top bar go to `Status -> Targets` to check exporter status. If the name is blue and `State` is `UP`, the exporter is running and Prometheus is successfully connected to the exporter.

####		5. On the top bar go to `Graph` and in the `Expression` box type `nv` to view all the metrics the exporter has.




##	3rd Grafana Setup:
	
####		1. After deployed Prometheus, open browser and go to:
			Grafana_Host:3000 (example: localhost:3000)

####		2. After login and add Prometheus source, find the `+` on the left bar, select `Import`

####		3. Upload our dashboard templet JSON file using the green bottom or copy the JSON file into the bigger box and load with the blue bottom.

####		4. You should get the dashboard and see data on it.

