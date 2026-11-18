# Phase 4 – Demo API Deployment & Observability Integration

**Project:** Kubernetes Observability Platform
**Phase:** 4
**Environment:** Local Kubernetes using Kind
**Namespace:** `demo-app`
**Monitoring:** Prometheus, Grafana, Alertmanager
**Logging:** Loki, Grafana Alloy
**Deployment:** Helm

---

## 1. Phase objectives

The objective of Phase 4 is to deploy the existing FastAPI Demo API into the Kubernetes cluster and verify that the complete observability pipeline works.

The phase covers:

1. Deploying the existing Docker image into Kind.
2. Creating a Helm chart for the application.
3. Deploying two API replicas.
4. Configuring Kubernetes health probes and resource limits.
5. Exposing application metrics through `/metrics`.
6. Configuring Prometheus scraping through a ServiceMonitor.
7. Collecting application logs through Grafana Alloy.
8. Querying application logs through Loki.
9. Visualizing metrics and logs in Grafana.
10. Testing application failures and Kubernetes events.
11. Configuring and testing Prometheus alerts.
12. Documenting the deployment and validation process.

### Existing infrastructure

The following components were established before Phase 4:

| Component | Namespace | Status before Phase 4 |
|---|---|---|
| kube-prometheus-stack | monitoring | Installed |
| Prometheus | monitoring | Installed |
| Grafana | monitoring | Installed |
| Alertmanager | monitoring | Installed |
| Node Exporter | monitoring | Installed |
| kube-state-metrics | monitoring | Installed |
| Loki | logging | Installed |
| Grafana Alloy | logging | Installed |
| Log generator | demo-app | Test workload |

Prometheus has the following ServiceMonitor selector:

```json
{"release":"monitoring"}
```

The ServiceMonitor namespace selector is:

```json
{}
```

This allows Prometheus to discover ServiceMonitors across namespaces, provided their labels match its selector.

### Existing application

The following work has already been completed:

- FastAPI application created.
- Application tested locally.
- Dockerfile created.
- Docker image built.
- Helm `values.yaml` created.
- Image loaded into Kind.

**Important:** The Docker image and `values.yaml` do not deploy the application. Helm needs a chart containing `Chart.yaml` and Kubernetes templates.

---

# 2. Verify the Kubernetes environment

## 2.1 Check the current context

Run:

```bash
kubectl config current-context
```

Expected:

```text
kind-monitoring-platform
```

Check the nodes:

```bash
kubectl get nodes
```

Expected:

```text
NAME                                STATUS   ROLES
monitoring-platform-control-plane   Ready    control-plane
```

The exact node names may differ if the cluster has multiple nodes.

## 2.2 Check namespaces

```bash
kubectl get namespaces
```

Verify that these namespaces exist:

```text
monitoring
logging
demo-app
```

If `demo-app` does not exist:

```bash
kubectl create namespace demo-app
```

## 2.3 Check the existing workloads

```bash
kubectl get pods -n monitoring
kubectl get pods -n logging
kubectl get pods -n demo-app
```

The log-generator pod may already be running in `demo-app`.

Do not remove existing workloads as part of this phase.

---

# 3. Verify the Docker image

The application image has already been built. We do not need to rebuild it unless a later code change requires a new image.

## 3.1 Inspect local Docker images

```bash
docker images
```

Find the Demo API image and note its exact repository and tag.

For example:

```text
REPOSITORY   TAG
demo-api     1.0.0
```

The example image reference is:

```text
demo-api:1.0.0
```

Use the actual image name and tag from your environment.

## 3.2 Verify the image in Kind

```bash
kind get nodes --name monitoring-platform
```

Check the image on the control-plane node:

```bash
docker exec monitoring-platform-control-plane \
  crictl images | grep demo-api
```

If the image is missing, load it:

```bash
kind load docker-image demo-api:1.0.0 \
  --name monitoring-platform
```

Replace the example image reference if your actual image name or tag differs.

Verify again:

```bash
docker exec monitoring-platform-control-plane \
  crictl images | grep demo-api
```

### Image pull policy

For a locally loaded image, use:

```yaml
image:
  repository: demo-api
  tag: "1.0.0"
  pullPolicy: IfNotPresent
```

This allows Kubernetes to use the image already available on the Kind node.

---

# 4. Create the Helm chart

## 4.1 Create the directory structure

From the project root:

```bash
mkdir -p infrastructure/helm/demo-api/templates
```

The final structure should be:

```text
infrastructure/helm/demo-api/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── servicemonitor.yaml
```

The existing `values.yaml` must be preserved and checked rather than blindly overwritten.

## 4.2 Create Chart.yaml

File:

`infrastructure/helm/demo-api/Chart.yaml`

```yaml
apiVersion: v2
name: demo-api
description: FastAPI application for Kubernetes observability testing
type: application
version: 0.1.0
appVersion: "1.0.0"
```

This file defines the Helm chart metadata.

## 4.3 Verify values.yaml

File:

`infrastructure/helm/demo-api/values.yaml`

The following is the expected example configuration:

```yaml
replicaCount: 2

image:
  repository: demo-api
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000
  targetPort: 8000

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

probes:
  liveness:
    path: /health
    initialDelaySeconds: 10
    periodSeconds: 10
  readiness:
    path: /ready
    initialDelaySeconds: 5
    periodSeconds: 5

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 15s
    labels:
      release: monitoring
```

Check that the image reference matches the image loaded into Kind.

## 4.4 Create deployment.yaml

File:

`infrastructure/helm/demo-api/templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Release.Namespace }}
  labels:
    app.kubernetes.io/name: demo-api
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app.kubernetes.io/name: demo-api
      app.kubernetes.io/instance: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: demo-api
        app.kubernetes.io/instance: {{ .Release.Name }}
    spec:
      containers:
        - name: demo-api
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: {{ .Values.probes.liveness.path }}
              port: http
            initialDelaySeconds: {{ .Values.probes.liveness.initialDelaySeconds }}
            periodSeconds: {{ .Values.probes.liveness.periodSeconds }}
          readinessProbe:
            httpGet:
              path: {{ .Values.probes.readiness.path }}
              port: http
            initialDelaySeconds: {{ .Values.probes.readiness.initialDelaySeconds }}
            periodSeconds: {{ .Values.probes.readiness.periodSeconds }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

The Deployment creates two API replicas and configures:

- Container image.
- Container port.
- Liveness probe.
- Readiness probe.
- CPU and memory requests.
- CPU and memory limits.

## 4.5 Create service.yaml

File:

`infrastructure/helm/demo-api/templates/service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Release.Namespace }}
  labels:
    app.kubernetes.io/name: demo-api
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  type: {{ .Values.service.type }}
  selector:
    app.kubernetes.io/name: demo-api
    app.kubernetes.io/instance: {{ .Release.Name }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
```

The Service provides a stable internal endpoint for the API pods.

## 4.6 Create servicemonitor.yaml

File:

`infrastructure/helm/demo-api/templates/servicemonitor.yaml`

```yaml
{{- if and .Values.monitoring.enabled .Values.monitoring.serviceMonitor.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Release.Namespace }}
  labels:
    app.kubernetes.io/name: demo-api
    app.kubernetes.io/instance: {{ .Release.Name }}
    {{- with .Values.monitoring.serviceMonitor.labels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  namespaceSelector:
    matchNames:
      - {{ .Release.Namespace }}
  selector:
    matchLabels:
      app.kubernetes.io/name: demo-api
      app.kubernetes.io/instance: {{ .Release.Name }}
  endpoints:
    - port: http
      path: /metrics
      interval: {{ .Values.monitoring.serviceMonitor.interval }}
{{- end }}
```

The ServiceMonitor tells Prometheus:

- Which Service to discover.
- Which endpoint to scrape.
- Which port to use.
- Which interval to use.
- Which namespace contains the Service.

The `release: monitoring` label is important because it matches the existing Prometheus selector.

---

# 5. Validate the Helm chart

Do not deploy before validating the chart.

## 5.1 Helm lint

```bash
helm lint infrastructure/helm/demo-api \
  --values infrastructure/helm/demo-api/values.yaml
```

Expected:

```text
1 chart(s) linted, 0 chart(s) failed
```

## 5.2 Render the manifests

```bash
helm template demo-api \
  infrastructure/helm/demo-api \
  --namespace demo-app \
  --values infrastructure/helm/demo-api/values.yaml
```

Check that the output contains:

- Deployment with two replicas.
- Correct image name and tag.
- Service on port 8000.
- Liveness and readiness probes.
- ServiceMonitor with `release: monitoring`.
- Metrics endpoint `/metrics`.

## 5.3 Check the ServiceMonitor CRD

```bash
kubectl get crd servicemonitors.monitoring.coreos.com
```

Expected: the CRD exists.

If the CRD does not exist, stop here and investigate the monitoring installation before deploying the chart.

---

# 6. Deploy Demo API with Helm

This is the actual application deployment step.

Run:

```bash
helm upgrade --install demo-api \
  infrastructure/helm/demo-api \
  --namespace demo-app \
  --create-namespace \
  --values infrastructure/helm/demo-api/values.yaml \
  --wait \
  --timeout 180s
```

Helm creates:

- Deployment.
- Two API pods.
- Service.
- ServiceMonitor.

## 6.1 Verify Helm release

```bash
helm list -n demo-app
```

Expected release:

```text
demo-api
```

## 6.2 Verify Deployment

```bash
kubectl get deployments -n demo-app
```

Expected:

```text
NAME       READY   UP-TO-DATE   AVAILABLE
demo-api   2/2     2            2
```

## 6.3 Verify pods

```bash
kubectl get pods -n demo-app -o wide
```

Expected:

```text
NAME                        READY   STATUS
demo-api-xxxxxxxxxx-xxxxx   1/1     Running
demo-api-xxxxxxxxxx-yyyyy   1/1     Running
```

The existing log-generator may also appear.

## 6.4 Verify Service

```bash
kubectl get services -n demo-app
```

Expected:

```text
NAME       TYPE        CLUSTER-IP
demo-api   ClusterIP   ...
```

## 6.5 Verify ServiceMonitor

```bash
kubectl get servicemonitors -n demo-app
```

Expected:

```text
NAME       AGE
demo-api   ...
```

Inspect it:

```bash
kubectl get servicemonitor demo-api \
  -n demo-app -o yaml
```

Verify the `release: monitoring` label and `/metrics` endpoint.

---

# 7. Inspect application logs

## 7.1 Get pod names

```bash
kubectl get pods -n demo-app
```

## 7.2 Inspect one API pod

```bash
kubectl logs <API-POD-NAME> -n demo-app --tail=100
```

## 7.3 Follow logs live

```bash
kubectl logs -f <API-POD-NAME> -n demo-app
```

## 7.4 Inspect all containers in the Deployment

```bash
kubectl logs deployment/demo-api \
  -n demo-app --all-pods=true --tail=100
```

If your kubectl version does not support this option, retrieve individual pod names and inspect them separately.

Look for:

- Application startup.
- Successful HTTP requests.
- HTTP 500 requests.
- Slow requests.
- JSON-formatted logs, if configured.

If the pod fails:

```bash
kubectl describe pod <API-POD-NAME> -n demo-app
```

Also inspect:

```bash
kubectl get events -n demo-app --sort-by=.lastTimestamp
```

---

# 8. Test the application endpoints

## 8.1 Start port-forward

In terminal 1:

```bash
kubectl port-forward -n demo-app \
  svc/demo-api 8000:8000
```

Leave this terminal running.

In terminal 2, test the API.

## 8.2 Health endpoint

```bash
curl -i http://localhost:8000/health
```

Expected:

```text
HTTP/1.1 200 OK
```

## 8.3 Readiness endpoint

```bash
curl -i http://localhost:8000/ready
```

Expected:

```text
HTTP/1.1 200 OK
```

## 8.4 Root endpoint

```bash
curl -i http://localhost:8000/
```

## 8.5 Hello endpoint

```bash
curl -i http://localhost:8000/hello
```

Both endpoints should return valid application responses.

## 8.6 Simulate an HTTP error

```bash
curl -i http://localhost:8000/simulate-error
```

Expected:

```text
HTTP/1.1 500 Internal Server Error
```

This is an intentional failure test.

## 8.7 Test slow requests

```bash
time curl -s http://localhost:8000/slow
```

If the endpoint is configured with a two-second delay, the request should take approximately two seconds.

---

# 9. Verify application metrics

## 9.1 Check the metrics endpoint

```bash
curl -s http://localhost:8000/metrics
```

Find the application metrics:

```bash
curl -s http://localhost:8000/metrics \
  | grep -E 'http_requests_total|http_request_duration_seconds'
```

Expected metric families, assuming the application uses the instrumentation configured for this project:

```text
http_requests_total
http_request_duration_seconds
```

Python process metrics may also appear:

```text
python_gc_objects_collected_total
process_cpu_seconds_total
process_resident_memory_bytes
```

## 9.2 Generate normal traffic

```bash
for i in {1..10}; do
  curl -s http://localhost:8000/hello > /dev/null
done
```

## 9.3 Generate HTTP 500 traffic

```bash
for i in {1..3}; do
  curl -s http://localhost:8000/simulate-error > /dev/null
done
```

## 9.4 Generate slow requests

```bash
for i in {1..3}; do
  curl -s http://localhost:8000/slow > /dev/null
done
```

## 9.5 Inspect metrics again

```bash
curl -s http://localhost:8000/metrics \
  | grep -E 'http_requests_total|http_request_duration_seconds'
```

Verify that:

- Successful requests are counted.
- HTTP 500 responses are counted.
- Request-duration histogram observations increase.

**Important:** Metric names and labels must be confirmed from the actual `/metrics` response. Do not assume that a particular label exists before inspecting it.

---

# 10. Verify Prometheus scraping

## 10.1 Verify the ServiceMonitor

```bash
kubectl get servicemonitor -n demo-app
```

Inspect:

```bash
kubectl get servicemonitor demo-api \
  -n demo-app -o yaml
```

Verify:

```yaml
labels:
  release: monitoring
```

And:

```yaml
endpoints:
  - port: http
    path: /metrics
```

## 10.2 Check the Prometheus selector

```bash
kubectl get prometheus monitoring-kube-prometheus-prometheus \
  -n monitoring \
  -o jsonpath='{.spec.serviceMonitorSelector.matchLabels}{"\n"}'
```

Expected:

```json
{"release":"monitoring"}
```

Check the namespace selector:

```bash
kubectl get prometheus monitoring-kube-prometheus-prometheus \
  -n monitoring \
  -o jsonpath='{.spec.serviceMonitorNamespaceSelector}{"\n"}'
```

Previously verified:

```json
{}
```

## 10.3 Open Prometheus

Start:

```bash
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open:

http://localhost:9090/targets

Find the Demo API target.

Expected state:

```text
UP
```

If the target is missing or DOWN, investigate:

```bash
kubectl get servicemonitor -n demo-app -o yaml
kubectl get svc -n demo-app --show-labels
kubectl get endpoints -n demo-app
kubectl get pods -n demo-app
```

The ServiceMonitor selector must match the Service labels, and the Service must have ready pod endpoints.

## 10.4 Test PromQL queries

### HTTP request rate

```promql
sum(rate(http_requests_total[5m]))
```

### HTTP 500 request rate

```promql
sum(rate(http_requests_total{status_code="500"}[5m]))
```

### Requests grouped by status code

```promql
sum by (status_code) (http_requests_total)
```

### Request latency p95

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

### Request latency p99

```promql
histogram_quantile(
  0.99,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

These queries assume the corresponding metric names and `status_code` label exist in the application. Adjust them if the actual metrics differ.

---

# 11. Verify Alloy and Loki logging

Alloy collects Kubernetes pod logs and forwards them to Loki.

We already verified that the log-generator workload was collected successfully.

Its working LogQL query was:

```logql
{instance="demo-app/log-generator:log-generator"}
```

This was discovered by inspecting Alloy logs rather than guessing the label.

## 11.1 Inspect Alloy logs

```bash
kubectl logs deployment/alloy \
  -n logging --since=15m
```

Filter for Demo API:

```bash
kubectl logs deployment/alloy \
  -n logging --since=15m \
  | grep -i demo-api
```

Look for target and label information.

For the log-generator, the relevant information included:

```text
target=demo-app/log-generator:log-generator
```

The full instance label was:

```text
demo-app/log-generator:log-generator
```

## 11.2 Find the Demo API instance label

First list the Demo API pods:

```bash
kubectl get pods -n demo-app
```

Then inspect Alloy logs:

```bash
kubectl logs deployment/alloy \
  -n logging --since=30m \
  | grep -i demo-api
```

Identify the actual `target` and `instance` values for the API pods.

Do not assume the instance label has the same value as the pod name.

## 11.3 Open Grafana Explore

Start Grafana port-forward:

```bash
kubectl port-forward -n monitoring \
  svc/monitoring-grafana 3000:80
```

Open:

http://localhost:3000/explore

Select Loki as the datasource.

Start by checking available streams:

```logql
{job="loki.source.kubernetes.pods"}
```

Then filter for Demo API using the actual label discovered from Alloy.

For example, if the instance value is confirmed to be `demo-app/demo-api-abc123:demo-api`:

```logql
{instance="demo-app/demo-api-abc123:demo-api"}
```

The example is illustrative. Replace it with the actual value from Alloy.

## 11.4 Check available labels

Use the Loki label browser in Grafana Explore, or query:

```logql
{instance=~".*demo-app.*"}
```

Remember that the earlier Loki installation did not expose a separate `namespace` label in its label list.

Do not rely on:

```logql
{namespace="demo-app"}
```

unless that label has actually been added to the stream.

## 11.5 Verify application log levels

The API should produce useful logs for:

- Successful requests.
- HTTP 500 errors.
- Slow requests.
- Application startup.

An HTTP 500 response does not automatically mean an ERROR-level log exists.

Check the application logging implementation and confirm that the deliberate error scenario writes an ERROR log.

If it only produces an INFO request log, update the application code before declaring error logging complete.

---

# 12. Verify Kubernetes metrics

The Kubernetes monitoring components provide information about pods, containers, deployments and nodes.

Use the following queries in Prometheus.

## 12.1 CPU usage

```promql
sum by (pod) (
  rate(container_cpu_usage_seconds_total{
    namespace="demo-app",
    container="demo-api"
  }[5m])
)
```

## 12.2 Memory usage

```promql
container_memory_working_set_bytes{
  namespace="demo-app",
  container="demo-api"
}
```

## 12.3 Pod readiness

```promql
kube_pod_status_ready{
  namespace="demo-app"
}
```

## 12.4 Container restarts

```promql
sum by (pod) (
  kube_pod_container_status_restarts_total{
    namespace="demo-app"
  }
)
```

## 12.5 Deployment replicas

```promql
kube_deployment_status_replicas_available{
  namespace="demo-app",
  deployment="demo-api"
}
```

If a metric is missing, verify that kube-state-metrics is running and that the metric is exposed in Prometheus before troubleshooting the query itself.

---

# 13. Test failure scenarios

These tests demonstrate that the observability platform detects problems rather than merely collecting normal traffic.

## 13.1 Test HTTP 500

Run:

```bash
curl -i http://localhost:8000/simulate-error
```

Verify:

1. API returns HTTP 500.
2. `http_requests_total` increases for status code 500.
3. Loki contains the associated application log.
4. Grafana can display the error information.

## 13.2 Test high latency

Run:

```bash
for i in {1..10}; do
  curl -s http://localhost:8000/slow > /dev/null
done
```

Verify:

- Request-duration histogram changes.
- p95 latency increases.
- Slow requests are visible in application logs.

## 13.3 Test pod replacement

Get API pods:

```bash
kubectl get pods -n demo-app
```

Choose one API pod and delete it:

```bash
kubectl delete pod <API-POD-NAME> -n demo-app
```

This is a controlled test. The Deployment controller should create a replacement pod.

Watch:

```bash
kubectl get pods -n demo-app -w
```

Verify:

- The deleted pod disappears.
- A replacement pod is created.
- The replacement becomes Ready.
- The Deployment returns to two available replicas.

Inspect events:

```bash
kubectl get events -n demo-app \
  --sort-by=.lastTimestamp
```

Do not delete the log-generator pod as a substitute for testing the API Deployment.

## 13.4 Test readiness failure

This test requires a controlled change to the readiness probe or application readiness behavior.

Before making changes:

```bash
kubectl get deployment demo-api -n demo-app -o yaml
```

A safe approach is to use a temporary Helm values override with an intentionally invalid readiness path, then restore the original values and upgrade again.

Do not permanently change the normal readiness endpoint.

Verify that:

- The affected pod becomes NotReady.
- The Service stops routing traffic to that pod.
- Prometheus shows the readiness change.
- The pod recovers after the original configuration is restored.

Only perform this test when you are ready to restore the normal configuration.

## 13.5 Test resource pressure

Do not deliberately exhaust resources on the cluster.

Instead, first observe the actual resource use:

```bash
kubectl top pods -n demo-app
kubectl describe deployment demo-api -n demo-app
```

If a resource-pressure test is required, use a separate temporary test workload with strict resource limits rather than destabilizing the monitoring stack.

---

# 14. Grafana dashboards

Create three dashboards.

## 14.1 Dashboard: Demo API Overview

Recommended panels:

| Panel | Query / source |
|---|---|
| Request rate | `sum(rate(http_requests_total[5m]))` |
| HTTP 5xx rate | `sum(rate(http_requests_total{status_code="500"}[5m]))` |
| Requests by status | `sum by (status_code) (http_requests_total)` |
| p95 latency | Histogram p95 query |
| p99 latency | Histogram p99 query |
| CPU usage | Container CPU query |
| Memory usage | Container memory query |

## 14.2 Dashboard: Kubernetes Health

Recommended panels:

- Pod readiness.
- Available Deployment replicas.
- Container restarts.
- CPU usage per pod.
- Memory usage per pod.
- Node CPU and memory.

## 14.3 Dashboard: Application Logs

Use Loki as the datasource.

Recommended panels:

- Application log stream.
- ERROR-level logs.
- HTTP 500 logs.
- Slow request logs.
- Logs filtered by API instance.

Use the actual labels discovered from Alloy.

Save dashboards in Grafana and export their JSON into the project repository:

```text
dashboards/
├── demo-api-overview.json
├── kubernetes-health.json
└── application-logs.json
```

---

# 15. Prometheus alerts

The platform should detect the following problems:

| Alert | Purpose |
|---|---|
| HighErrorRate | Too many HTTP 5xx responses |
| HighRequestLatency | High p95 latency |
| PodCrashLooping | Container repeatedly crashes |
| PodNotReady | Application pod is not ready |
| HighCPUUsage | High container CPU usage |
| HighMemoryUsage | High container memory usage |

## 15.1 Check PrometheusRule selector

Before creating rules, inspect the existing Prometheus configuration:

```bash
kubectl get prometheus monitoring-kube-prometheus-prometheus \
  -n monitoring \
  -o jsonpath='{.spec.ruleSelector.matchLabels}{"\n"}'
```

Also inspect:

```bash
kubectl get prometheus monitoring-kube-prometheus-prometheus \
  -n monitoring \
  -o jsonpath='{.spec.ruleNamespaceSelector}{"\n"}'
```

The rules must have labels and be placed in a namespace that the existing Prometheus instance selects.

Do not assume that the ServiceMonitor selector automatically applies to PrometheusRule objects.

## 15.2 Create the alert rules

After checking the selectors, create:

`infrastructure/kubernetes/monitoring/demo-api-alerts.yaml`

Example:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: demo-api-alerts
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
    - name: demo-api
      rules:
        - alert: HighErrorRate
          expr: |
            (
              sum(rate(http_requests_total{status_code=~"5.."}[5m]))
              /
              clamp_min(sum(rate(http_requests_total[5m])), 0.001)
            ) > 0.05
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: High HTTP error rate
            description: More than 5 percent of API requests are returning HTTP 5xx.

        - alert: HighRequestLatency
          expr: |
            histogram_quantile(
              0.95,
              sum by (le) (
                rate(http_request_duration_seconds_bucket[5m])
              )
            ) > 1
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: High API request latency
            description: API p95 request latency is above one second.

        - alert: PodCrashLooping
          expr: |
            kube_pod_container_status_waiting_reason{
              namespace="demo-app",
              reason="CrashLoopBackOff"
            } > 0
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: Demo API pod is crash looping
            description: A container in the demo-app namespace is in CrashLoopBackOff.

        - alert: PodNotReady
          expr: |
            kube_pod_status_ready{
              namespace="demo-app",
              condition="true"
            } == 0
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: Demo API pod is not ready
            description: A pod in demo-app is not Ready.

        - alert: HighCPUUsage
          expr: |
            sum by (pod) (
              rate(container_cpu_usage_seconds_total{
                namespace="demo-app",
                container="demo-api"
              }[5m])
            ) > 0.4
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: High Demo API CPU usage
            description: Demo API container CPU usage is above 0.4 CPU cores.

        - alert: HighMemoryUsage
          expr: |
            container_memory_working_set_bytes{
              namespace="demo-app",
              container="demo-api"
            } > 201326592
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: High Demo API memory usage
            description: Demo API container memory usage is above 192 MiB.
```

These are example thresholds for the project's configured resource limits. Adjust them based on observed behavior.

The `status_code` label and histogram names must match the actual application metrics.

## 15.3 Validate and apply

Check that the CRD exists:

```bash
kubectl get crd prometheusrules.monitoring.coreos.com
```

Validate the YAML:

```bash
kubectl apply --dry-run=server \
  -f infrastructure/kubernetes/monitoring/demo-api-alerts.yaml
```

If validation succeeds:

```bash
kubectl apply \
  -f infrastructure/kubernetes/monitoring/demo-api-alerts.yaml
```

Verify:

```bash
kubectl get prometheusrules -n monitoring
```

## 15.4 Verify alert evaluation

Open:

http://localhost:9090/alerts

Check that the rules are loaded.

Generate HTTP 500 requests:

```bash
for i in {1..50}; do
  curl -s http://localhost:8000/simulate-error > /dev/null
done
```

The error-rate alert should become Pending and then Firing if the configured threshold and `for` duration are satisfied.

Check Alertmanager:

```bash
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-alertmanager 9093:9093
```

Open:

http://localhost:9093

**Important:** A Prometheus alert reaching Firing does not automatically prove that an email, Slack message or other notification was delivered. Notification routing and receivers must be configured and tested separately.

---

# 16. Troubleshooting

## 16.1 Pod stuck in ImagePullBackOff

Inspect:

```bash
kubectl describe pod <API-POD-NAME> -n demo-app
```

Verify the image:

```bash
docker exec monitoring-platform-control-plane \
  crictl images | grep demo-api
```

If missing:

```bash
kind load docker-image demo-api:1.0.0 \
  --name monitoring-platform
```

Check that the image reference in `values.yaml` matches the loaded image.

## 16.2 Pod stuck in CrashLoopBackOff

Inspect:

```bash
kubectl logs <API-POD-NAME> -n demo-app
```

Previous container:

```bash
kubectl logs <API-POD-NAME> -n demo-app --previous
```

Describe:

```bash
kubectl describe pod <API-POD-NAME> -n demo-app
```

## 16.3 Service has no endpoints

```bash
kubectl get svc demo-api -n demo-app
kubectl get endpoints demo-api -n demo-app
kubectl get pods -n demo-app --show-labels
```

The Service selector must match the pod labels.

## 16.4 Prometheus target missing

```bash
kubectl get servicemonitor -n demo-app -o yaml
kubectl get svc demo-api -n demo-app --show-labels
kubectl get endpoints demo-api -n demo-app
```

Verify:

- ServiceMonitor has `release: monitoring`.
- ServiceMonitor selects the Demo API Service.
- Service has ready endpoints.
- ServiceMonitor uses port `http`.
- `/metrics` is available.

## 16.5 Loki does not show API logs

Inspect Alloy:

```bash
kubectl logs deployment/alloy -n logging --since=30m
```

Filter:

```bash
kubectl logs deployment/alloy \
  -n logging --since=30m | grep -i demo-api
```

Inspect API logs directly:

```bash
kubectl logs deployment/demo-api \
  -n demo-app --all-pods=true --tail=100
```

Find the actual instance label from Alloy and use it in Grafana Explore.

Remember the working log-generator query:

```logql
{instance="demo-app/log-generator:log-generator"}
```

Do not assume the Demo API will have the same instance label.

## 16.6 Metrics missing

Check:

```bash
curl -s http://localhost:8000/metrics
```

Then check the Prometheus target state at:

http://localhost:9090/targets

If the target is UP but a particular metric is missing, inspect the actual `/metrics` output and verify that the corresponding code path has executed.

## 16.7 Helm release status

```bash
helm status demo-api -n demo-app
helm history demo-api -n demo-app
```

Render again:

```bash
helm template demo-api \
  infrastructure/helm/demo-api \
  --namespace demo-app \
  --values infrastructure/helm/demo-api/values.yaml
```

---

# 17. Useful operational commands

## Deployment

```bash
helm upgrade --install demo-api \
  infrastructure/helm/demo-api \
  --namespace demo-app \
  --values infrastructure/helm/demo-api/values.yaml \
  --wait
```

## Rollout status

```bash
kubectl rollout status deployment/demo-api -n demo-app
```

## Rollout history

```bash
kubectl rollout history deployment/demo-api -n demo-app
```

## Restart deployment

```bash
kubectl rollout restart deployment/demo-api -n demo-app
```

## Get all application resources

```bash
kubectl get all -n demo-app
```

## Application logs

```bash
kubectl logs deployment/demo-api -n demo-app --all-pods=true --tail=100
```

## Application events

```bash
kubectl get events -n demo-app --sort-by=.lastTimestamp
```

## Helm release

```bash
helm status demo-api -n demo-app
```

---

# 18. Git repository structure after Phase 4

The expected project structure is:

```text
kubernetes-observability-platform/
├── applications/
│   └── demo-api/
│       ├── app/
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── infrastructure/
│   ├── helm/
│   │   ├── monitoring/
│   │   ├── demo-api/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   └── templates/
│   │   │       ├── deployment.yaml
│   │   │       ├── service.yaml
│   │   │       └── servicemonitor.yaml
│   │   └── logging/
│   │       ├── loki/
│   │       └── alloy/
│   │
│   └── kubernetes/
│       └── monitoring/
│           └── demo-api-alerts.yaml
│
├── dashboards/
│   ├── demo-api-overview.json
│   ├── kubernetes-health.json
│   └── application-logs.json
│
└── docs/
    ├── architecture.md
    ├── installation.md
    ├── logging.md
    ├── troubleshooting.md
    └── phase-4-demo-api-observability.md
```

---

# 19. Commit Phase 4

Before committing, inspect changes:

```bash
git status
```

Validate the Helm chart:

```bash
helm lint infrastructure/helm/demo-api
```

Review the files:

```bash
git diff --stat
```

Stage the relevant files:

```bash
git add infrastructure/helm/demo-api
git add infrastructure/kubernetes/monitoring/demo-api-alerts.yaml
git add dashboards/
git add docs/phase-4-demo-api-observability.md
```

Commit:

```bash
git commit -m "feat: deploy demo API and integrate observability"
```

Push:

```bash
git push
```

Only stage files that actually exist and have been reviewed.

---

# 20. Definition of Done

Phase 4 is complete when the following items have been verified.

## Application deployment

- [ ] Existing Docker image is available in Kind.
- [ ] Helm chart has been created.
- [ ] Helm lint succeeds.
- [ ] Helm template renders correctly.
- [ ] Demo API is deployed through Helm.
- [ ] Two API replicas are Running.
- [ ] Both replicas are Ready.
- [ ] Kubernetes Service has endpoints.
- [ ] Health and readiness probes work.

## Application metrics

- [ ] `/metrics` responds successfully.
- [ ] HTTP requests are counted.
- [ ] HTTP 200 requests are visible.
- [ ] HTTP 500 requests are visible.
- [ ] Request latency histogram is populated.
- [ ] Prometheus target is UP.
- [ ] PromQL queries return results.

## Application logs

- [ ] Alloy discovers the API pods.
- [ ] API logs reach Loki.
- [ ] Actual instance labels have been identified.
- [ ] INFO logs are visible.
- [ ] ERROR logs are visible.
- [ ] HTTP 500 requests can be correlated with logs.
- [ ] Slow requests can be identified.

## Kubernetes monitoring

- [ ] CPU metrics are available.
- [ ] Memory metrics are available.
- [ ] Pod readiness is available.
- [ ] Container restart metrics are available.
- [ ] Deployment replica metrics are available.
- [ ] Pod replacement test succeeds.

## Grafana and alerts

- [ ] Demo API dashboard created.
- [ ] Kubernetes health dashboard created.
- [ ] Application logs dashboard created.
- [ ] Prometheus alert rules loaded.
- [ ] At least one alert has been triggered and verified in Alertmanager.
- [ ] Notification delivery tested if a receiver is configured.

## Documentation and Git

- [ ] Phase 4 documentation saved.
- [ ] Helm chart committed.
- [ ] Alert rules committed.
- [ ] Dashboards exported and committed.
- [ ] Git changes pushed to GitHub.

---

# 21. Phase 4 completion summary

At the end of this phase, the platform should have a real application running inside Kubernetes, with application-level and infrastructure-level observability.

The complete data flow should be:

```text
                 DEMO API
                    |
          ---------------------
          |                   |
       /metrics            Application logs
          |                   |
          v                   v
      Prometheus           Grafana Alloy
          |                   |
          |                   v
          |                  Loki
          |                   |
          v                   v
       Grafana <------------- Grafana
          |
          v
       Alerting
          |
          v
     Alertmanager
```

The result is a working demonstration of how Kubernetes workloads can be monitored, how application errors can be investigated, and how operational problems can be detected through metrics, logs and alerts.

**Phase 4 should only be marked complete after the Definition of Done has been verified against the actual cluster.**