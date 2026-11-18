# Monitoring and Alerting

## Overview

The platform uses Prometheus, Grafana, Loki and Alloy
to provide metrics, dashboards, log collection and alerting

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
- Log volume Logs by pod
- Recent errors

## Prometheus

| Alert | Threshold | Severity |
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