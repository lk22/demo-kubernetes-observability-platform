# Phase 5 – Grafana Dashboards & Alerting

## 1. Overview

The objective of Phase 5 is to build a complete observability and alerting layer for the Kubernetes Observability Platform.

This phase extends the existing monitoring and logging infrastructure with Grafana dashboards, Prometheus alert rules, alert evaluation and alert validation.

The goal is to make it possible to:

- Monitor application performance.
- Monitor Kubernetes cluster health.
- Investigate application and infrastructure logs.
- Detect abnormal conditions automatically.
- Validate alert rules through controlled tests.
- Store dashboards and alert configurations in Git.
- Document the monitoring and alerting architecture.

### 1.1 Architecture

The observability architecture consists of:

| Component | Responsibility |
|---|---|
| Demo API | Generates application metrics and logs |
| Prometheus | Collects and stores metrics |
| Grafana | Visualizes metrics and logs |
| Loki | Stores application and Kubernetes logs |
| Alloy | Collects and forwards logs |
| Prometheus Operator | Manages Prometheus resources and alert rules |
| PrometheusRule | Defines custom alert rules |
| Alertmanager | Groups, routes and manages notifications |

### 1.2 Prerequisites

The following components must already be installed and operational:

- Kubernetes Kind cluster.
- Helm.
- Prometheus.
- Grafana.
- Prometheus Operator.
- Loki.
- Grafana Alloy.
- Demo API.
- Prometheus ServiceMonitor for Demo API.
- Grafana Prometheus datasource.
- Grafana Loki datasource.

The following namespaces are used:

```text
monitoring
logging
demo-app
```

The existing Kubernetes clusters and application data must be preserved throughout this phase.

---

# 2. Phase Structure

Phase 5 consists of the following activities:

| Step | Activity |
|---|---|
| 5.1 | Demo API Overview Dashboard |
| 5.2 | Kubernetes Cluster Overview Dashboard |
| 5.3 | Logs & Error Investigation Dashboard |
| 5.4 | Create Prometheus alert rules |
| 5.5 | Install and verify PrometheusRule |
| 5.6 | Configure Grafana alert visibility |
| 5.7 | Test alert conditions |
| 5.8 | Configure and validate Alertmanager |
| 5.9 | Version dashboards and alert rules |
| 5.10 | Document monitoring and alerting |
| 5.11 | Final validation |

---

# 3. Step 5.1 – Demo API Overview Dashboard

## Objective

Create a Grafana dashboard for monitoring the Demo API.

The dashboard provides visibility into request traffic, HTTP errors and application latency.

## Dashboard name

```text
Demo API Overview
```

## Panels

### Panel 1 – Request Rate

Visualization: Time series

Datasource: Prometheus

PromQL:

```promql
sum(rate(http_requests_total[5m]))
```

Purpose:

Displays the number of HTTP requests per second.

### Panel 2 – Error Rate

Visualization: Time series

Datasource: Prometheus

PromQL:

```promql
100 *
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
clamp_min(sum(rate(http_requests_total[5m])), 0.000000001)
```

Purpose:

Displays the percentage of HTTP 5xx responses.

Unit: Percent (0-100).

### Panel 3 – HTTP 5xx Errors

Visualization: Time series

Datasource: Prometheus

PromQL:

```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

Purpose:

Displays the rate of HTTP server errors.

### Panel 4 – P95 Request Latency

Visualization: Time series

Datasource: Prometheus

PromQL:

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
) * 1000
```

Purpose:

Displays the 95th percentile request latency in milliseconds.

### Panel 5 – Total Requests

Visualization: Stat

Datasource: Prometheus

PromQL:

```promql
sum(http_requests_total)
```

Purpose:

Displays the total number of requests collected by Prometheus.

## Dashboard settings

Recommended settings:

```text
Time range: Last 15 minutes
Refresh interval: 15 seconds
```

## Validation

- Confirm that request traffic is visible.
- Generate test requests if necessary.
- Confirm that HTTP 5xx responses appear when `/simulate-error` is called.
- Confirm that latency increases when `/slow` is called.
- Confirm that all panels use the Prometheus datasource.

---

# 4. Step 5.2 – Kubernetes Cluster Overview Dashboard

## Objective

Create a dashboard that provides an overview of Kubernetes cluster health and resource consumption.

## Dashboard name

```text
Kubernetes Cluster Overview
```

## Panels

### Panel 1 – Node CPU Usage

Visualization: Time series

PromQL:

```promql
100 * (
  1 - avg by (instance) (
    rate(node_cpu_seconds_total{mode="idle"}[5m])
  )
)
```

Purpose:

Displays CPU utilization per node.

Unit: Percent (0-100).

### Panel 2 – Node Memory Usage

Visualization: Time series

PromQL:

```promql
100 * (
  1 -
  node_memory_MemAvailable_bytes
  /
  node_memory_MemTotal_bytes
)
```

Purpose:

Displays node memory utilization.

Unit: Percent (0-100).

### Panel 3 – Running Pods

Visualization: Stat

PromQL:

```promql
sum(kube_pod_status_phase{phase="Running"})
```

Purpose:

Displays the number of pods in Running phase.

### Panel 4 – Pod Restarts

Visualization: Stat

PromQL:

```promql
sum(increase(kube_pod_container_status_restarts_total[1h]))
```

Purpose:

Displays the number of container restarts during the last hour.

### Panel 5 – Pod Status

Visualization: Pie chart

PromQL:

```promql
sum by (phase) (
  kube_pod_status_phase
)
```

Purpose:

Displays the distribution of Kubernetes pod phases.

### Panel 6 – CPU Usage by Namespace

Visualization: Time series

PromQL:

```promql
sum by (namespace) (
  rate(container_cpu_usage_seconds_total{
    container!="",
    container!="POD"
  }[5m])
)
```

Purpose:

Displays CPU consumption grouped by namespace.

Unit: Cores.

### Panel 7 – Memory Usage by Namespace

Visualization: Time series

PromQL:

```promql
sum by (namespace) (
  container_memory_working_set_bytes{
    container!="",
    container!="POD"
  }
)
```

Purpose:

Displays memory consumption grouped by namespace.

Unit: Bytes (IEC).

## Validation

- Confirm that node CPU metrics are available.
- Confirm that node memory metrics are available.
- Confirm that kube-state-metrics provides pod status metrics.
- Confirm that container CPU and memory metrics are available.
- Verify that namespace grouping works.

Note:

Some metrics depend on kubelet/cAdvisor and kube-state-metrics. An empty panel does not automatically mean Grafana is malfunctioning. Verify the metric in Prometheus first.

---

# 5. Step 5.3 – Logs & Error Investigation Dashboard

## Objective

Create a dashboard for application log investigation using Loki.

The dashboard provides access to Demo API logs and makes it easier to investigate application errors.

## Dashboard name

```text
Logs & Error Investigation
```

## Datasource

```text
Loki
```

## Important: Verify the Loki labels

The Loki installation uses Kubernetes log collection through Grafana Alloy.

Previously observed labels include:

```text
instance
job
pod
service_name
stream
```

The exact label values must be verified in Grafana Explore.

The following example identifies a Demo API container:

```logql
{instance="demo-app/demo-app-75f75f9bf9-tdm8b:demo-api"}
```

The pod name is an example. Kubernetes can generate a different pod name after a replacement or rollout.

## Panel 1 – Application Logs

Visualization: Logs

LogQL:

```logql
{instance=~"demo-app/.+:demo-api"}
```

Purpose:

Displays logs from Demo API containers matching the instance label pattern.

## Panel 2 – Error Logs

Visualization: Logs

LogQL:

```logql
{instance=~"demo-app/.+:demo-api"}
|~ "(?i)error|exception|traceback|critical"
```

Purpose:

Filters application log lines using common error keywords.

Note:

This is a text-based filter. HTTP 500 responses are not necessarily included unless the application writes matching error messages to its logs.

## Panel 3 – Log Volume

Visualization: Time series

LogQL:

```logql
sum(
  count_over_time(
    {instance=~"demo-app/.+:demo-api"}[5m]
  )
)
```

Purpose:

Displays the number of matching log lines over a rolling five-minute window.

## Panel 4 – Logs by Pod

Visualization: Time series

LogQL:

```logql
sum by (instance) (
  count_over_time(
    {instance=~"demo-app/.+:demo-api"}[5m]
  )
)
```

Legend:

```text
{{instance}}
```

Purpose:

Compares log activity between Demo API instances.

## Panel 5 – Recent Errors

Visualization: Logs

LogQL:

```logql
{instance=~"demo-app/.+:demo-api"}
|~ "(?i)error|exception|traceback|critical"
```

Purpose:

Displays recent application log lines matching the error filter.

## Validation

- Confirm that Loki is selected as the datasource.
- Confirm that Demo API logs appear in Explore.
- Verify the instance label.
- Generate application traffic if no recent logs exist.
- Confirm that the Log Volume panel returns data.
- Confirm that error filtering works when matching log messages exist.

---

# 6. Step 5.4 – Create Prometheus Alert Rules

## Objective

Create custom Prometheus alert rules for application and Kubernetes monitoring.

The rules are defined as Kubernetes resources using the PrometheusRule custom resource.

## Alert rules

The platform uses six custom alert rules.

| Alert | Condition | Severity |
|---|---|---|
| HighErrorRate | HTTP 5xx rate above 5% | warning |
| HighRequestLatency | P95 latency above 1 second | warning |
| PodCrashLooping | Container in CrashLoopBackOff | critical |
| PodNotReady | Pod not ready for 5 minutes | warning |
| HighCPUUsage | Pod CPU usage above 0.4 cores | warning |
| HighMemoryUsage | Pod memory usage above 192 MiB | warning |

## Step 1 – Create the directory

From the repository root:

```bash
mkdir -p infrastructure/kubernetes/monitoring/alerts
```

## Step 2 – Create the alert file

File:

```text
infrastructure/kubernetes/monitoring/alerts/prometheus-rules.yaml
```

Configuration:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: platform-alerts
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
    - name: demo-api-alerts
      rules:
        - alert: HighErrorRate
          expr: |
            (
              sum(rate(http_requests_total{status_code=~"5.."}[5m]))
              /
              clamp_min(sum(rate(http_requests_total[5m])), 0.000001)
            ) > 0.05
          for: 2m
          labels:
            severity: warning
            component: demo-api
          annotations:
            summary: "Demo API has a high HTTP 5xx error rate"
            description: "More than 5% of API requests have returned HTTP 5xx errors for at least 2 minutes."

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
            component: demo-api
          annotations:
            summary: "Demo API request latency is high"
            description: "The API p95 request latency has exceeded 1 second for at least 2 minutes."

    - name: kubernetes-alerts
      rules:
        - alert: PodCrashLooping
          expr: |
            max by (namespace, pod, container) (
              kube_pod_container_status_waiting_reason{
                reason="CrashLoopBackOff"
              }
            ) == 1
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Container is crash looping"
            description: "Container {{ $labels.container }} in pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is in CrashLoopBackOff."

        - alert: PodNotReady
          expr: |
            sum by (namespace, pod) (
              kube_pod_status_ready{condition="false"}
            ) == 1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Kubernetes pod is not ready"
            description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} has been not ready for 5 minutes."

        - alert: HighCPUUsage
          expr: |
            sum by (namespace, pod) (
              rate(container_cpu_usage_seconds_total{
                container!="",
                container!="POD"
              }[5m])
            ) > 0.4
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod CPU usage is high"
            description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is using more than 0.4 CPU cores."

        - alert: HighMemoryUsage
          expr: |
            sum by (namespace, pod) (
              container_memory_working_set_bytes{
                container!="",
                container!="POD"
              }
            ) > 201326592
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod memory usage is high"
            description: "Pod {{ $labels.pod }} in namespace {{ $labels.namespace }} is using more than 192 MiB of memory."
```

## Step 3 – Understand the configuration

### apiVersion

```yaml
apiVersion: monitoring.coreos.com/v1
```

Identifies the Prometheus Operator API.

### kind

```yaml
kind: PrometheusRule
```

Defines a Prometheus alert or recording rule resource.

### namespace

```yaml
namespace: monitoring
```

Places the resource in the monitoring namespace.

### labels

```yaml
labels:
  release: monitoring
```

The label is intended to match the Prometheus rule selector.

Always verify the actual selector in the Prometheus custom resource.

### expr

Defines the PromQL expression evaluated by Prometheus.

### for

Defines how long the condition must remain true before the alert becomes firing.

### severity

Defines the alert severity.

### annotations

Provides human-readable descriptions for the alert.

## Step 4 – Validate the YAML

```bash
kubectl apply --dry-run=client \
  -f infrastructure/kubernetes/monitoring/alerts/prometheus-rules.yaml
```

Expected output:

```text
prometheusrule.monitoring.coreos.com/platform-alerts created (dry run)
```

---

# 7. Step 5.5 – Install and Verify PrometheusRule

## Step 1 – Install the alert rules

```bash
kubectl apply \
  -f infrastructure/kubernetes/monitoring/alerts/prometheus-rules.yaml
```

Expected output:

```text
prometheusrule.monitoring.coreos.com/platform-alerts created
```

## Step 2 – Verify the resource

```bash
kubectl get prometheusrules -n monitoring
```

Expected result:

```text
NAME              AGE
platform-alerts   ...
```

## Step 3 – Inspect the resource

```bash
kubectl describe prometheusrule platform-alerts -n monitoring
```

Verify:

- All six alert rules are present.
- The alert names are correct.
- The severity labels are present.
- The expressions are present.
- The evaluation periods are correct.

## Step 4 – Verify Prometheus rule selectors

```bash
kubectl get prometheus -n monitoring
```

Inspect the Prometheus resource:

```bash
kubectl get prometheus -n monitoring -o yaml
```

Check:

```yaml
spec:
  ruleSelector:
  ruleNamespaceSelector:
```

The Prometheus instance must select the labels and namespace containing the PrometheusRule resource.

A resource can exist in Kubernetes without being loaded by Prometheus.

## Step 5 – Open Prometheus

Start port forwarding:

```bash
kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-prometheus \
  9090:9090
```

Open:

```text
http://localhost:9090
```

Navigate to:

```text
Status → Rules
```

Verify the groups:

```text
demo-api-alerts
kubernetes-alerts
```

## Step 6 – Verify alert states

Navigate to:

```text
Alerts
```

Possible states:

| State | Meaning |
|---|---|
| Inactive | Alert condition is not currently met |
| Pending | Condition is met, but the for-period has not elapsed |
| Firing | Condition has remained true long enough |

It is normal for alerts to start in Inactive state.

---

# 8. Step 5.6 – Grafana Alert Visibility

## Objective

Use Grafana to inspect alert information and monitor the state of the observability platform.

Open Grafana:

```text
http://localhost:3000
```

Navigate to:

```text
Alerting → Alert rules
```

Inspect the available rules and datasource integration.

Important:

Prometheus-managed rules and Grafana-managed alert rules are different alerting mechanisms.

The platform uses Prometheus as its primary rule evaluation engine. Do not recreate all six rules as Grafana-managed rules unless there is a specific reason to introduce a second alerting engine.

Grafana can use the Prometheus datasource to inspect alert information.

## Validation

- Verify Prometheus is configured as a datasource.
- Verify that Prometheus alerts are visible through the available Grafana integration.
- Verify that no duplicate alert rules have been created accidentally.

---

# 9. Step 5.7 – Test Alert Conditions

## Objective

Validate that the alert rules respond to controlled test conditions.

Testing should not require deleting or modifying existing clusters or production-like application resources.

Use temporary test workloads only.

## Test A – HighErrorRate

Objective:

Generate HTTP 500 responses from Demo API.

The endpoint is:

```text
/simulate-error
```

Start a temporary test pod:

```bash
kubectl run alert-test \
  -n demo-app \
  --image=curlimages/curl:8.12.1 \
  --restart=Never \
  --rm -i \
  -- sh -c '
    i=0
    while [ "$i" -lt 1000 ]; do
      curl -sS -o /dev/null \
        http://demo-app:8002/simulate-error
      i=$((i+1))
      sleep 0.2
    done
  '
```

The request loop generates sustained HTTP 500 traffic.

Inspect the error ratio in Prometheus:

```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
clamp_min(sum(rate(http_requests_total[5m])), 0.000001)
```

Expected behavior:

- The ratio exceeds 0.05.
- Prometheus marks HighErrorRate as Pending.
- After the two-minute hold period, it becomes Firing if the condition remains true.

The test may need to run for several minutes because the query uses a five-minute rate window.

Stop the test if necessary with Ctrl+C. If the pod remains, remove it:

```bash
kubectl delete pod alert-test -n demo-app --ignore-not-found
```

## Test B – HighRequestLatency

Objective:

Generate slow API requests.

The endpoint is:

```text
/slow
```

Run:

```bash
kubectl run latency-test \
  -n demo-app \
  --image=curlimages/curl:8.12.1 \
  --restart=Never \
  --rm -i \
  -- sh -c '
    i=0
    while [ "$i" -lt 100 ]; do
      curl -sS -o /dev/null \
        http://demo-app:8002/slow
      i=$((i+1))
    done
  '
```

The endpoint should take approximately two seconds per request.

Inspect the P95 latency:

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

Expected behavior:

- P95 latency exceeds one second.
- HighRequestLatency becomes Pending.
- It becomes Firing after two minutes if the condition remains true.

Because the query uses a five-minute window, allow enough time for traffic to populate the histogram.

## Test C – PodCrashLooping

Objective:

Verify that Kubernetes container crashes are detected.

Create a temporary crash-looping pod:

```bash
kubectl run crash-test \
  -n demo-app \
  --image=busybox:1.36 \
  --restart=Always \
  -- sh -c 'exit 1'
```

Inspect:

```bash
kubectl get pods -n demo-app -w
```

Expected state:

```text
CrashLoopBackOff
```

Verify the metric in Prometheus:

```promql
kube_pod_container_status_waiting_reason{
  reason="CrashLoopBackOff"
} == 1
```

Expected behavior:

- PodCrashLooping becomes Pending.
- It becomes Firing after two minutes.

Remove the temporary pod:

```bash
kubectl delete pod crash-test -n demo-app
```

## Test D – PodNotReady

Objective:

Verify that pods that are not ready are detected.

Create a temporary pod:

```bash
kubectl run readiness-test \
  -n demo-app \
  --image=busybox:1.36 \
  --restart=Never \
  -- sh -c 'sleep 3600'
```

Add a readiness probe that intentionally fails:

```bash
kubectl patch pod readiness-test \
  -n demo-app \
  --type=json \
  -p='[
    {
      "op":"add",
      "path":"/spec/containers/0/readinessProbe",
      "value":{
        "httpGet":{
          "path":"/does-not-exist",
          "port":8080
        },
        "initialDelaySeconds":1,
        "periodSeconds":5
      }
    }
  ]'
```

Inspect:

```bash
kubectl get pod readiness-test -n demo-app
```

Expected state:

```text
0/1 Running
```

Verify in Prometheus:

```promql
sum by (namespace, pod) (
  kube_pod_status_ready{condition="false"}
) == 1
```

Expected behavior:

- PodNotReady becomes Pending.
- It becomes Firing after five minutes if the pod remains not ready.

Remove the test pod:

```bash
kubectl delete pod readiness-test -n demo-app
```

## Test E – HighCPUUsage

Objective:

Validate CPU metrics and the HighCPUUsage alert.

Check that CPU metrics are available:

```promql
container_cpu_usage_seconds_total
```

Inspect CPU consumption:

```promql
sum by (namespace, pod) (
  rate(container_cpu_usage_seconds_total{
    container!="",
    container!="POD"
  }[5m])
)
```

The configured alert threshold is:

```text
0.4 CPU cores
```

The condition must remain true for five minutes.

Optional controlled test:

```bash
kubectl run cpu-test \
  -n demo-app \
  --image=busybox:1.36 \
  --restart=Never \
  -- sh -c 'while true; do :; done'
```

Observe CPU consumption in Prometheus.

Remove the temporary pod:

```bash
kubectl delete pod cpu-test -n demo-app
```

Note:

The Kind cluster's available CPU resources may prevent this test pod from reaching the threshold. Do not assume an inactive alert is broken without checking the actual metric values.

## Test F – HighMemoryUsage

Objective:

Validate memory metrics and the HighMemoryUsage alert.

Check:

```promql
container_memory_working_set_bytes
```

Inspect memory usage:

```promql
sum by (namespace, pod) (
  container_memory_working_set_bytes{
    container!="",
    container!="POD"
  }
)
```

Configured threshold:

```text
192 MiB
```

The condition must remain true for five minutes.

The memory test is optional. Do not allocate large amounts of memory on a resource-constrained local cluster just to force the alert to fire.

If the alert is not tested with a controlled workload, document it as query-validated rather than load-tested.

---

# 10. Step 5.8 – Alertmanager

## Objective

Verify that Prometheus alerts are forwarded to Alertmanager.

Alertmanager is responsible for:

- Grouping alerts.
- Routing alerts.
- Managing notification receivers.
- Handling silences and inhibition rules.

## Step 1 – Verify Alertmanager pods

```bash
kubectl get pods -n monitoring | grep alertmanager
```

## Step 2 – Verify Alertmanager services

```bash
kubectl get svc -n monitoring | grep alertmanager
```

## Step 3 – Start port forwarding

A common kube-prometheus-stack service is:

```bash
kubectl port-forward \
  -n monitoring \
  svc/alertmanager-operated \
  9093:9093
```

If this service is not present, inspect the output of the service command and use the actual Alertmanager service name.

Open:

```text
http://localhost:9093
```

## Step 4 – Verify alerts

Check that firing Prometheus alerts are visible in Alertmanager.

Verify:

- Alert names.
- Severity labels.
- Namespace and pod labels where applicable.
- Alert state.

## Step 5 – Notification configuration

Notification receivers can be configured for:

- Email.
- Slack.
- Other supported integrations.

The receiver configuration must be managed securely.

Never commit passwords, SMTP credentials or API tokens to GitHub.

For the local platform, notification delivery can be treated as an optional extension if no SMTP or external notification service has been configured.

---

# 11. Step 5.9 – Version Control

## Objective

Store Grafana dashboards and Prometheus alert rules in Git.

This makes monitoring configuration reproducible and suitable for future GitOps deployment.

## Step 1 – Export Grafana dashboards

For each dashboard:

1. Open the dashboard.
2. Open Dashboard settings or the Share/Export menu.
3. Select Export.
4. Export the dashboard as JSON.
5. Save the file in the repository.

Recommended structure:

```text
dashboards/
├── demo-api-overview.json
├── kubernetes-cluster-overview.json
└── logs-error-investigation.json
```

## Step 2 – Verify alert configuration

Ensure the following file exists:

```text
infrastructure/kubernetes/monitoring/alerts/prometheus-rules.yaml
```

## Step 3 – Inspect repository changes

```bash
git status
```

Review the changes:

```bash
git diff --stat
```

Check that no secrets or credentials are included.

## Step 4 – Validate the alert YAML

```bash
kubectl apply --dry-run=client \
  -f infrastructure/kubernetes/monitoring/alerts/prometheus-rules.yaml
```

## Step 5 – Commit the changes

```bash
git add dashboards/
git add infrastructure/kubernetes/monitoring/alerts/
```

Commit:

```bash
git commit -m "Add Grafana dashboards and Prometheus alert rules"
```

Push:

```bash
git push origin main
```

Use the correct branch name if the repository does not use main.

Note:

Dashboard JSON can contain datasource UIDs. These may need to be mapped when importing dashboards into another Grafana installation.

---

# 12. Step 5.10 – Documentation

## Objective

Document the monitoring and alerting architecture.

Create:

```text
docs/monitoring-and-alerting.md
```

Recommended content:

```markdown
# Monitoring and Alerting

## Overview

The platform uses Prometheus, Grafana, Loki and Alloy
to provide metrics, dashboards, log collection and alerting.

## Grafana Dashboards

### Demo API Overview
- HTTP request rate
- HTTP error rate
- Request latency
- Total requests

### Kubernetes Cluster Overview
- Node CPU usage
- Node memory usage
- Running pods
- Pod restarts
- Namespace resource usage

### Logs & Error Investigation
- Application logs
- Error logs
- Log volume
- Logs by pod
- Recent errors

## Prometheus Alert Rules

| Alert | Threshold | Severity |
|---|---|---|
| HighErrorRate | > 5% HTTP 5xx | warning |
| HighRequestLatency | P95 > 1 second | warning |
| PodCrashLooping | CrashLoopBackOff | critical |
| PodNotReady | Not ready for 5 minutes | warning |
| HighCPUUsage | > 0.4 CPU cores | warning |
| HighMemoryUsage | > 192 MiB | warning |

## Alert Lifecycle

Prometheus evaluates alert rules.
Alertmanager groups and routes notifications.
Grafana provides dashboards and alert visibility.

## Validation

- [ ] PrometheusRule exists
- [ ] Prometheus loads all alert rules
- [ ] Alerts appear in Prometheus
- [ ] Alertmanager receives firing alerts
- [ ] Grafana dashboards display metrics and logs
- [ ] Test resources are removed

## Troubleshooting

### Alerts are not visible
Check Prometheus rule selectors and namespace selectors.

### Alerts remain inactive
Check metric availability, query results and alert thresholds.

### Notifications are not delivered
Check Alertmanager configuration and receiver credentials.
```

---

# 13. Step 5.11 – Final Validation

The final validation confirms that all observability components work together.

## Kubernetes validation

```bash
kubectl get nodes
```

```bash
kubectl get pods -n monitoring
```

```bash
kubectl get pods -n logging
```

```bash
kubectl get pods -n demo-app
```

Verify that expected workloads are Running and Ready.

## Prometheus validation

Open:

```text
http://localhost:9090
```

Check:

- Status → Targets
- Status → Rules
- Alerts

Verify that Demo API metrics are being collected and all six custom alert rules are loaded.

## Grafana validation

Open:

```text
http://localhost:3000
```

Verify the dashboards:

- Demo API Overview.
- Kubernetes Cluster Overview.
- Logs & Error Investigation.

Confirm that the expected metrics and logs are displayed.

## Loki validation

In Grafana Explore, select Loki and execute:

```logql
{instance=~"demo-app/.+:demo-api"}
```

Verify that Demo API logs are visible.

## PrometheusRule validation

```bash
kubectl get prometheusrule platform-alerts -n monitoring
```

## Test resource cleanup

```bash
kubectl get pods -n demo-app
```

Remove any remaining temporary test pods:

```bash
kubectl delete pod alert-test -n demo-app --ignore-not-found
kubectl delete pod latency-test -n demo-app --ignore-not-found
kubectl delete pod crash-test -n demo-app --ignore-not-found
kubectl delete pod readiness-test -n demo-app --ignore-not-found
kubectl delete pod cpu-test -n demo-app --ignore-not-found
kubectl delete pod memory-test -n demo-app --ignore-not-found
```

Only temporary test pods created during this phase should be removed.

Do not delete application workloads or existing namespaces.

---

# 14. Definition of Done

Phase 5 is considered complete when the following requirements have been met.

## Dashboards

- [ ] Demo API Overview dashboard created and validated.
- [ ] Kubernetes Cluster Overview dashboard created and validated.
- [ ] Logs & Error Investigation dashboard created and validated.
- [ ] Demo API logs are visible through Loki.

## Prometheus alerting

- [ ] PrometheusRule resource created.
- [ ] PrometheusRule resource installed in Kubernetes.
- [ ] Prometheus rule selectors verified.
- [ ] All six alert rules loaded by Prometheus.
- [ ] HighErrorRate validated.
- [ ] HighRequestLatency validated.
- [ ] PodCrashLooping validated.
- [ ] PodNotReady validated.
- [ ] HighCPUUsage validated.
- [ ] HighMemoryUsage validated.

## Alertmanager

- [ ] Alertmanager is running.
- [ ] Prometheus alerts are visible in Alertmanager.
- [ ] Notification configuration reviewed.
- [ ] Notification delivery tested if a receiver is configured.

## Git and documentation

- [ ] Dashboard JSON files exported.
- [ ] Prometheus alert rules stored in Git.
- [ ] Monitoring documentation created.
- [ ] Git changes reviewed.
- [ ] Changes committed and pushed to GitHub.

## Cleanup

- [ ] Temporary test workloads removed.
- [ ] Existing application workloads remain operational.
- [ ] Existing Kubernetes clusters and data preserved.

---

# 15. Expected Repository Structure

After completing Phase 5, the relevant repository structure should look similar to this:

```text
kubernetes-observability-platform/
│
├── applications/
│   └── demo-api/
│
├── infrastructure/
│   ├── helm/
│   │   ├── monitoring/
│   │   ├── logging/
│   │   │   ├── loki/
│   │   │   └── alloy/
│   │   └── demo-api/
│   │
│   └── kubernetes/
│       └── monitoring/
│           └── alerts/
│               └── prometheus-rules.yaml
│
├── dashboards/
│   ├── demo-api-overview.json
│   ├── kubernetes-cluster-overview.json
│   └── logs-error-investigation.json
│
└── docs/
    ├── monitoring-and-alerting.md
    └── phase-5-monitoring-and-alerting.md
```

---

# 16. Troubleshooting Reference

| Problem | Possible cause | What to check |
|---|---|---|
| Dashboard shows No data | Metric unavailable | Query metric in Prometheus |
| Loki query returns no logs | Wrong datasource or labels | Check Loki Explore and labels |
| Alert rules missing | Prometheus selector mismatch | Inspect ruleSelector |
| Alerts stay inactive | Threshold not reached | Inspect PromQL result |
| Alerts stay pending | for-period not elapsed | Check alert duration |
| CrashLoop alert missing | Pod has not reached CrashLoopBackOff | Inspect pod status and metric |
| CPU alert missing | CPU usage below threshold | Inspect CPU query |
| Memory alert missing | Memory below threshold | Inspect memory query |
| Alertmanager has no alerts | Prometheus-to-Alertmanager integration issue | Inspect Prometheus configuration and targets |
| Notifications not delivered | Receiver configuration issue | Inspect Alertmanager configuration |

---

# 17. Phase Completion

After successful validation, the platform has:

- Application-level metrics.
- Kubernetes infrastructure metrics.
- Centralized application logging.
- Grafana dashboards.
- Prometheus-based alert rules.
- Alertmanager integration.
- Version-controlled monitoring configuration.
- Monitoring and alerting documentation.

Phase 5 establishes the observability foundation required for the next stage of the project.

**Next phase: Phase 6 – GitOps with Argo CD**

The next phase introduces GitOps workflows, automated synchronization and declarative deployment management.
