from prometheus_client import start_http_server, Metric, REGISTRY
from datetime import datetime
import json
import requests
import sys
import time
import urllib3
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
iusername = 'admin'
ipassword = 'admin'

class apiCollector(object):
  def __init__(self, endpoint):
    self._endpoint = endpoint
  def collect(self):
    for target in self._endpoint:
        ep1 = target.split(':')
        ep = ep1[0]
  
    #Login and get token
        data = '{"password": {"username": "'+iusername+'", "password": "'+ipassword+'"}}'
        headers = {'Content-Type': 'application/json'}
        response = requests.post('https://' +target+ '/v1/auth', headers=headers, data=data, verify=False)
        token = json.loads(response.text)["token"]["token"]
        headers = {'Content-Type': 'application/json','X-Auth-Token': token}
    
    #Get system summary
        response = requests.get('https://' +target+ '/v1/system/summary', headers=headers, verify=False)
        sjson = json.loads(response.text)
        #Set summary metrics
        metric = Metric('nv_summary', 'A summary of ' +ep, 'summary')
        metric.add_sample('nv_summary_services', value=sjson["summary"]["services"], labels={'target':ep})
        metric.add_sample('nv_summary_policy', value=sjson["summary"]["policy_rules"], labels={'target':ep})
        metric.add_sample('nv_summary_runningWorkloads', value=sjson["summary"]["running_workloads"], labels={'target':ep})
        metric.add_sample('nv_summary_totalWorkloads', value=sjson["summary"]["workloads"], labels={'target':ep})
        metric.add_sample('nv_summary_hosts', value=sjson["summary"]["hosts"], labels={'target':ep})
        metric.add_sample('nv_summary_controllers', value=sjson["summary"]["controllers"], labels={'target':ep})
        metric.add_sample('nv_summary_enforcers', value=sjson["summary"]["enforcers"], labels={'target':ep})
        metric.add_sample('nv_summary_pods', value=sjson["summary"]["running_pods"], labels={'target': ep})
        metric.add_sample('nv_summary_disconnectedEnforcers', value=sjson["summary"]["disconnected_enforcers"], labels={'target': ep})
        metric.add_sample('nv_summary_cvedbVersion', value=sjson["summary"]["cvedb_version"], labels={'target':ep})
        #Convert time, set CVEDB create time
        dt = sjson["summary"]["cvedb_create_time"]
        dt1 = dt.split('-')#Year, Mon
        dt2 = dt1[2].split('T')#Day
        dt3 = dt2[1].split(':')#Hour, Min
        dt4 = dt3[2].split('Z')#Sec
        ap = 'AM'
        if int(dt3[0]) > 12:
            ap = 'PM'
            dt3[0] = int(dt3[0]) - 12
        time0 = datetime.strptime('12 31 1969  5:00:00PM', '%m %d %Y %I:%M:%S%p')
        time1 = dt1[1]+' '+dt2[0]+' '+dt1[0]+'  '+dt3[0]+':'+dt3[1]+':'+dt4[0]+ap
        time2 = datetime.strptime(time1, '%m %d %Y %I:%M:%S%p')
        diff = int((time2 - time0).total_seconds()*1000)
        metric.add_sample('nv_summary_cvedbTime', value=diff, labels={'target':ep})
        yield metric

    #Get conversation
        response = requests.get('https://' +target+ '/v1/conversation', headers=headers, verify=False)
        #Set conversation metrics    
        metric = Metric('nv_conversation', 'conversation of ' +ep, 'gauge')
        for c in json.loads(response.text)['conversations']:
            try: c['ports']
            except KeyError: port_exists = False
            else: port_exists = True
            if port_exists is True:
                for k in c['ports']: 
                    if c['bytes'] is not 0:
                        metric.add_sample('nv_conversation_bytes', value=c['bytes'], labels={'port': k, 'from': c['from'], 'to': c['to'], 'target':ep})
        yield metric

    #Get enforcer
        response = requests.get('https://' +target+ '/v1/enforcer', headers=headers, verify=False)
        #Read each enforcer, set enforcer metrics    
        metric = Metric('nv_enforcer', 'enforcers of ' +ep, 'gauge')
        for c in json.loads(response.text)['enforcers']:
            response2 = requests.get('https://' +target+ '/v1/enforcer/' + c['id'] + '/stats', headers=headers, verify=False)
            ejson = json.loads(response2.text)
            metric.add_sample('nv_enforcer_cpu', value=ejson['stats']['span_1']['cpu'], labels={'id': c['id'], 'host': c['host_name'], 'display': c['display_name'], 'target':ep})
            metric.add_sample('nv_enforcer_memory', value=ejson['stats']['span_1']['memory'], labels={'id': c['id'], 'host': c['host_name'], 'display': c['display_name'], 'target':ep})
        yield metric

    #Get host
        response = requests.get('https://' +target+ '/v1/host', headers=headers, verify=False)
        #Set host metrics    
        metric = Metric('nv_host', 'host information of ' +ep, 'gauge')
        for c in json.loads(response.text)['hosts']:
            metric.add_sample('nv_host_memory', value=c['memory'], labels={'name': c['name'], 'id': c['id'], 'target':ep})
        yield metric

    #Get debug admission stats
        response = requests.get('https://' +target+ '/v1/debug/admission_stats', headers=headers, verify=False)
        djson = json.loads(response.text)
        #Set admission metrics
        metric = Metric('nv_admission', 'Debug admission stats of ' +ep, 'gauge')
        metric.add_sample('nv_admission_allowed', value=djson['stats']['k8s_allowed_requests'], labels={'target':ep})
        metric.add_sample('nv_admission_denied', value=djson['stats']['k8s_denied_requests'], labels={'target':ep})
        yield metric

    #Get image vulnerability
        response = requests.get('https://' +target+ '/v1/scan/registry', headers=headers, verify=False)
        #Set vulnerability metrics    
        metric = Metric('nv_image_vulnerability', 'image vulnerability of ' +ep, 'gauge')
        for c in json.loads(response.text)['summarys']:
            response2 = requests.get('https://' +target+ '/v1/scan/registry/' + c['name'] + '/images', headers=headers, verify=False)
            for i in json.loads(response2.text)['images']:
                metric.add_sample('nv_image_vulnerabilityHigh', value=i['high'], labels={'name': c['name'], 'imageid': i['image_id'], 'target':ep})
                metric.add_sample('nv_image_vulnerabilityMedium', value=i['medium'], labels={'name': c['name'], 'imageid': i['image_id'], 'target':ep})
        yield metric

    #Get container vulnerability
        response = requests.get('https://' +target+ '/v1/scan/workload', headers=headers, verify=False)
        #Set vulnerability metrics  
        cvlist = []
        metric = Metric('nv_container_vulnerability', 'container vulnerability of ' +ep, 'gauge')
        for c in json.loads(response.text)['workloads']:
            if c['service'] not in cvlist and c['service_mesh_sidecar'] is False and c['high']!=0 and c['medium']!=0:
                if ("-pod-" not in c['service'] and "default" not in c['service']) or "-pod-00" in c['service']  or "-v1" in c['service']:
                    metric.add_sample('nv_container_vulnerabilityHigh', value=c['high'], labels={'service': c['service'], 'target':ep})
                    metric.add_sample('nv_container_vulnerabilityMedium', value=c['medium'], labels={'service': c['service'], 'target':ep})
                    cvlist.append(c['service'])
        yield metric

    # Set Log metrics
        metric = Metric('nv_log', 'log of ' +ep, 'gauge')
    #Get log threat
        response = requests.get('https://' +target+ '/v1/log/threat', headers=headers, verify=False)
        #Set threat
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
        for x in range(0,5):
            metric.add_sample('nv_log_events', value=ttimelist[x]*1000, labels={'log': "thread", 'fromname': tcnamelist[x], 'toname': " -> " +tsnamelist[x], 'id': tidlist[x], 'name': tnamelist[x], 'target':ep})
        
    #Get log incident
        response = requests.get('https://' +target+ '/v1/log/incident', headers=headers, verify=False)       
        #Set incident metrics
        itimelist = []
        inamelist = []
        iwnamelist = []
        iidlist = []
        for c in json.loads(response.text)['incidents']:
            try: c['workload_name']
            except KeyError: workload_exists = False
            else: workload_exists = True
            if workload_exists is True:
                itimelist.append(c['reported_timestamp'])
                inamelist.append(c['name'])
                iwnamelist.append(c['workload_name'])
                iidlist.append(c['workload_id'])
        for x in range(0,5):
            metric.add_sample('nv_log_events', value=itimelist[x]*1000, labels={'log': "incident", 'fromname': iwnamelist[x], 'toname': " ", 'name': inamelist[x], 'id': iidlist[x], 'target':ep})

    #Get log violation
        response = requests.get('https://' +target+ '/v1/log/violation', headers=headers, verify=False)
        #Set violation metrics
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
                vidlist.append(c['client_id']+c['server_id'])
        for x in range(0,5):
            metric.add_sample('nv_log_events', value=vtimelist[x]*1000, labels={'log': "violation", 'id': vidlist[x], 'toname': " -> " +vsnamelist[x], 'fromname': vcnamelist[x], 'name': vnamelist[x],  'target': ep})
        yield metric

    #Logout
        response = requests.delete('https://' +target+ '/v1/auth', headers=headers, verify=False)


if __name__ == '__main__':
  # Usage: exporter.py -e export -s target -u username -p password
  # example: python3 nv_exporter.py -e 1234 -s 10.1.22.11:30443 -s 10.1.22.12:30443 -u admin -p admin
  parser = argparse.ArgumentParser(description='NeuVector command line.')
  parser.add_argument("-e", "--export", type=int, help="controller export")
  parser.add_argument("-s", "--server", action='append', help="controller IP address")
  parser.add_argument("-u", "--username", type=str, help="username")
  parser.add_argument("-p", "--password", type=str, help="password")
  argss = parser.parse_args()

  if argss.export and argss.server:
    if argss.username and argss.password:
      iusername = argss.username
      ipassword = argss.password
    start_http_server(argss.export)
    REGISTRY.register(apiCollector(argss.server))

  while True: time.sleep(30)

