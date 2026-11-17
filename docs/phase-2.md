# phase two

The process of this phase is to install all necessary monitonring tools into your cluster in the monitoring namespace

# 1 install kube-prometheus-stack

we are going to install following tools
- Prometheus
- Grafana
- Alertmanager
- Node exporter
- kube-state-metrics
- Prometheus Operator

firstly we install kube-prometheus-stack
```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 93.3.1 \
  --namespace monitoring \
  --values infrastructure/helm/monitoring/values.yaml \
  --wait \
  --timeout 10m
```

if it dont work with the wait and timeout flag, you can simply remove them
but we need to make sure that the status says Deployed when it finishes

## 2 Control helm installation

To control we have installed the resources into your cluster
run following commands
```bash
helm list -n monitoring
```
# Control pods in the cluster

Here we control we have all the neccessary pods in the monitoring namespace
```bash
kubect get pods -n monitoring -o wide
```

We make sure that Status of all the pods is Ready and have 2/2 or 3/3 or how many replicas they make but make sure all pods and replicas is ready and created
**
## 4 Control services**
We also need to control that all services in the namespace are running

```bash
kubectl get svc -n monitoring
```

you should get related services for
- Grafana
- Prometheus
- Alertmanager
- kube-state-metrics
- Node Exporter

## control persistent storage

To control all persisten storages or PVC's we need to list them first by running

```bash
kubectl get pvc -n monitoring
```

## 6 Open Grafana

If grafana is running in the cluster namespace we can open the tool in the browser by bind the service to a port by running the port-forward command

```bash
kubectl port-forward svc/monitor-grafana <PORT | 3000>:80 -n monitoring
```

this makes sure you can open grafana on your specified port
http://localhst:<specified_port>

A default admin login consists of the username "admin"
you can retrieve the password by following command
```bash
kubectl get secret grafana-admin-password -n monitoring -o jsonpath='{.data.admin-password}' | base64 --decode
echo
```

this will grab the secret password and decode the base64 value to give you the password to login with

## 7 Open Prometheus
firstly make sure the prometheus services are running in your cluster

then in your browser, test it works by entering http://localhost:9090
in the query page try to query following PromQL query "up"

this will tell you what is up and running in your cluster and what it can scrape metrics from

## Control Prometheus targets

in Prometheus, go to Status and choose targets and control that the target pods gets status "UP"
you should see pods like Node Exporter and kube-state-metrics

## 9 Control Grafana dashboards
Here we need to follow up on 4 Grafana dashboards
- Kubernetes / Compute Resource / Cluster
- Kubernetes /Compute Resources / Node
- Kubernetes /Compute Resources / Namespace
- Node Exporter / Node

Theese dashboards shows essential data for your cluster, Nodes and namespaces and nodes

## Finishing control
when installation is done and you know everything works
make a final control

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
kubectl get pvc -n monitoring
helm status monitoring -n monitoring
```