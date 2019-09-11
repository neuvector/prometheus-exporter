from datetime import datetime
from prometheus_client import start_http_server, Metric, REGISTRY
import argparse
import json
import os
import requests
import signal
import sys
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()


class apiCollector(object):
    def __init__(self, endpoint):
        self._endpoint = endpoint
        self._url = "https://" + endpoint

    def sigterm_handler(self, _signo, _stack_frame):
        print("Logout ...")
        session.delete(self._url + '/v1/auth')
        sys.exit(0)

    def collect(self):
        eps = self._endpoint.split(':')
        ep = eps[0]

        # Get system summary
        try:
            response = session.get(self._url + '/v1/system/summary',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            sjson = json.loads(response.text)
            # Set summary metrics
            metric = Metric('nv_summary', 'A summary of ' + ep, 'summary')
            metric.add_sample('nv_summary_services',
                              value=sjson["summary"]["services"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_policy',
                              value=sjson["summary"]["policy_rules"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_runningWorkloads',
                              value=sjson["summary"]["running_workloads"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_totalWorkloads',
                              value=sjson["summary"]["workloads"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_hosts',
                              value=sjson["summary"]["hosts"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_controllers',
                              value=sjson["summary"]["controllers"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_enforcers',
                              value=sjson["summary"]["enforcers"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_pods',
                              value=sjson["summary"]["running_pods"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_disconnectedEnforcers',
                              value=sjson["summary"]["disconnected_enforcers"],
                              labels={'target': ep})
            metric.add_sample('nv_summary_cvedbVersion',
                              value=sjson["summary"]["cvedb_version"],
                              labels={'target': ep})
            # Convert time, set CVEDB create time
            dt = sjson["summary"]["cvedb_create_time"]
            if not dt:
                metric.add_sample('nv_summary_cvedbTime',
                                  value=0,
                                  labels={'target': ep})
            else:
                dt1 = dt.split('-')  #Year, Mon
                dt2 = dt1[2].split('T')  #Day
                dt3 = dt2[1].split(':')  #Hour, Min
                dt4 = dt3[2].split('Z')  #Sec
                ap = 'AM'
                if int(dt3[0]) > 12:
                    ap = 'PM'
                    dt3[0] = int(dt3[0]) - 12
                time0 = datetime.strptime('12 31 1969  5:00:00PM',
                                          '%m %d %Y %I:%M:%S%p')
                time1 = dt1[1] + ' ' + dt2[0] + ' ' + dt1[0] + '  ' + dt3[
                    0] + ':' + dt3[1] + ':' + dt4[0] + ap
                time2 = datetime.strptime(time1, '%m %d %Y %I:%M:%S%p')
                diff = int((time2 - time0).total_seconds() * 1000)
                metric.add_sample('nv_summary_cvedbTime',
                                  value=diff,
                                  labels={'target': ep})
            yield metric

        # Get conversation
        try:
            response = session.get(self._url + '/v1/conversation',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set conversation metrics
            metric = Metric('nv_conversation', 'conversation of ' + ep,
                            'gauge')
            for c in json.loads(response.text)['conversations']:
                try:
                    c['ports']
                except KeyError:
                    port_exists = False
                else:
                    port_exists = True
                if port_exists is True:
                    for k in c['ports']:
                        if c['bytes'] is not 0:
                            metric.add_sample('nv_conversation_bytes',
                                              value=c['bytes'],
                                              labels={
                                                  'port': k,
                                                  'from': c['from'],
                                                  'to': c['to'],
                                                  'target': ep
                                              })
            yield metric

        # Get enforcer
        try:
            response = session.get(self._url + '/v1/enforcer', verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Read each enforcer, set enforcer metrics
            metric = Metric('nv_enforcer', 'enforcers of ' + ep, 'gauge')
            for c in json.loads(response.text)['enforcers']:
                response2 = session.get(self._url + '/v1/enforcer/' + c['id'] +
                                        '/stats',
                                        verify=False)
                ejson = json.loads(response2.text)
                metric.add_sample('nv_enforcer_cpu',
                                  value=ejson['stats']['span_1']['cpu'],
                                  labels={
                                      'id': c['id'],
                                      'host': c['host_name'],
                                      'display': c['display_name'],
                                      'target': ep
                                  })
                metric.add_sample('nv_enforcer_memory',
                                  value=ejson['stats']['span_1']['memory'],
                                  labels={
                                      'id': c['id'],
                                      'host': c['host_name'],
                                      'display': c['display_name'],
                                      'target': ep
                                  })
            yield metric

        # Get host
        try:
            response = session.get(self._url + '/v1/host', verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set host metrics
            metric = Metric('nv_host', 'host information of ' + ep, 'gauge')
            for c in json.loads(response.text)['hosts']:
                metric.add_sample('nv_host_memory',
                                  value=c['memory'],
                                  labels={
                                      'name': c['name'],
                                      'id': c['id'],
                                      'target': ep
                                  })
            yield metric

        # Get debug admission stats
        try:
            response = session.get(self._url + '/v1/debug/admission_stats',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            if response.status_code != 200:
                print("Admission control stats request failed: %s" % response)
            else:
                djson = json.loads(response.text)
                # Set admission metrics
                metric = Metric('nv_admission', 'Debug admission stats of ' + ep,
                                'gauge')
                metric.add_sample('nv_admission_allowed',
                                  value=djson['stats']['k8s_allowed_requests'],
                                  labels={'target': ep})
                metric.add_sample('nv_admission_denied',
                                  value=djson['stats']['k8s_denied_requests'],
                                  labels={'target': ep})
                yield metric

        # Get image vulnerability
        try:
            response = session.get(self._url + '/v1/scan/registry',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set vulnerability metrics
            metric = Metric('nv_image_vulnerability',
                            'image vulnerability of ' + ep, 'gauge')
            for c in json.loads(response.text)['summarys']:
                try:
                    response2 = session.get(self._url + '/v1/scan/registry/' +
                                            c['name'] + '/images',
                                            verify=False)
                except requests.exceptions.RequestException as e:
                    print(e)
                else:
                    for i in json.loads(response2.text)['images']:
                        metric.add_sample('nv_image_vulnerabilityHigh',
                                          value=i['high'],
                                          labels={
                                              'name': c['name'],
                                              'imageid': i['image_id'],
                                              'target': ep
                                          })
                        metric.add_sample('nv_image_vulnerabilityMedium',
                                          value=i['medium'],
                                          labels={
                                              'name': c['name'],
                                              'imageid': i['image_id'],
                                              'target': ep
                                          })
            yield metric

        # Get container vulnerability
        try:
            response = session.get(self._url + '/v1/scan/workload',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set vulnerability metrics
            cvlist = []
            metric = Metric('nv_container_vulnerability',
                            'container vulnerability of ' + ep, 'gauge')
            for c in json.loads(response.text)['workloads']:
                if c['service'] not in cvlist and c[
                        'service_mesh_sidecar'] is False and c[
                            'high'] != 0 and c['medium'] != 0:
                    if (
                            "-pod-" not in c['service']
                            and "default" not in c['service']
                    ) or "-pod-00" in c['service'] or "-v1" in c['service']:
                        metric.add_sample('nv_container_vulnerabilityHigh',
                                          value=c['high'],
                                          labels={
                                              'service': c['service'],
                                              'target': ep
                                          })
                        metric.add_sample('nv_container_vulnerabilityMedium',
                                          value=c['medium'],
                                          labels={
                                              'service': c['service'],
                                              'target': ep
                                          })
                        cvlist.append(c['service'])
            yield metric

        # Set Log metrics
        metric = Metric('nv_log', 'log of ' + ep, 'gauge')
        # Get log threat
        try:
            response = session.get(self._url + '/v1/log/threat', verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set threat
            ttimelist = []
            tnamelist = []
            tcnamelist = []
            tsnamelist = []
            tidlist = []
            for c in json.loads(response.text)['threats']:
                ttimelist.append(c['reported_timestamp'])
                tnamelist.append(c['name'])
                tcnamelist.append(c['client_workload_name'])
                tsnamelist.append(c['server_workload_name'])
                tidlist.append(c['id'])
            for x in range(0, min(5, len(tidlist))):
                metric.add_sample('nv_log_events',
                                  value=ttimelist[x] * 1000,
                                  labels={
                                      'log': "thread",
                                      'fromname': tcnamelist[x],
                                      'toname': " -> " + tsnamelist[x],
                                      'id': tidlist[x],
                                      'name': tnamelist[x],
                                      'target': ep
                                  })

        # Get log incident
        try:
            response = session.get(self._url + '/v1/log/incident',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set incident metrics
            itimelist = []
            inamelist = []
            iwnamelist = []
            iidlist = []
            for c in json.loads(response.text)['incidents']:
                try:
                    c['workload_name']
                except KeyError:
                    workload_exists = False
                else:
                    workload_exists = True
                if workload_exists is True:
                    itimelist.append(c['reported_timestamp'])
                    inamelist.append(c['name'])
                    iwnamelist.append(c['workload_name'])
                    iidlist.append(c['workload_id'])
            for x in range(0, min(5, len(iidlist))):
                metric.add_sample('nv_log_events',
                                  value=itimelist[x] * 1000,
                                  labels={
                                      'log': "incident",
                                      'fromname': iwnamelist[x],
                                      'toname': " ",
                                      'name': inamelist[x],
                                      'id': iidlist[x],
                                      'target': ep
                                  })

        # Get log violation
        try:
            response = session.get(self._url + '/v1/log/violation',
                                   verify=False)
        except requests.exceptions.RequestException as e:
            print(e)
        else:
            # Set violation metrics
            vtimelist = []
            vnamelist = []
            vcnamelist = []
            vsnamelist = []
            vidlist = []
            for c in json.loads(response.text)['violations']:
                vtimelist.append(c['reported_timestamp'])
                vcnamelist.append(c['client_name'])
                vnamelist.append(c['cluster_name'])
                vsnamelist.append(c['server_name'])
                vidlist.append(c['client_id'] + c['server_id'])
            for x in range(0, min(5, len(vidlist))):
                metric.add_sample('nv_log_events',
                                  value=vtimelist[x] * 1000,
                                  labels={
                                      'log': "violation",
                                      'id': vidlist[x],
                                      'toname': " -> " + vsnamelist[x],
                                      'fromname': vcnamelist[x],
                                      'name': vnamelist[x],
                                      'target': ep
                                  })
            yield metric


ENV_CTRL_API_SVC = "CTRL_API_SERVICE"
ENV_CTRL_USERNAME = "CTRL_USERNAME"
ENV_CTRL_PASSWORD = "CTRL_PASSWORD"
ENV_EXPORTER_PORT = "EXPORTER_PORT"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NeuVector command line.')
    parser.add_argument("-e", "--port", type=int, help="exporter port")
    parser.add_argument("-s",
                        "--server",
                        type=str,
                        help="controller API service")
    parser.add_argument("-u",
                        "--username",
                        type=str,
                        help="controller user name")
    parser.add_argument("-p",
                        "--password",
                        type=str,
                        help="controller user password")
    argss = parser.parse_args()

    if argss.server:
        ctrl_svc = argss.server
    elif ENV_CTRL_API_SVC in os.environ:
        ctrl_svc = os.environ.get(ENV_CTRL_API_SVC)
    else:
        sys.exit("Controller API service endpoint must be specified.")

    if argss.port:
        port = argss.port
    elif ENV_EXPORTER_PORT in os.environ:
        port = int(os.environ.get(ENV_EXPORTER_PORT))
    else:
        sys.exit("Exporter port must be specified.")

    if argss.username:
        ctrl_user = argss.username
    elif ENV_CTRL_USERNAME in os.environ:
        ctrl_user = os.environ.get(ENV_CTRL_USERNAME)
    else:
        ctrl_user = "admin"

    if argss.password:
        ctrl_pass = argss.password
    elif ENV_CTRL_PASSWORD in os.environ:
        ctrl_pass = os.environ.get(ENV_CTRL_PASSWORD)
    else:
        ctrl_pass = "admin"

    # Login and get token
    print("Login to controller ...")
    data = '{"password": {"username": "' + ctrl_user + '", "password": "' + ctrl_pass + '"}}'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post('https://' + ctrl_svc + '/v1/auth',
                                 headers=headers,
                                 data=data,
                                 verify=False)
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)

    if response.status_code != 200:
        message = json.loads(response.text)["message"]
        print(message)
        sys.exit(1)

    token = json.loads(response.text)["token"]["token"]

    # Create request session
    session.headers.update({"Content-Type": "application/json"})
    session.headers.update({'X-Auth-Token': token})

    print("Start exporter server ...")
    start_http_server(port)

    print("Register collector ...")
    collector = apiCollector(ctrl_svc)
    REGISTRY.register(collector)
    signal.signal(signal.SIGTERM, collector.sigterm_handler)

    while True:
        time.sleep(30)
