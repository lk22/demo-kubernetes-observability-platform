# Architecture

### Overview
The kubernetes Observability Platform provides centralized monitoring, logging and alerting for Kubernetes workloads

### Core Components

#### Metrics

Prometheus collects metrics from Kubernetes nodes, workloads and applications

#### Visualization

Grafana provides dashboards and operational visibility

#### Alerting

alertmanager handles alert routing and notifications.

#### Logging

Loki stores and indexes application and infrastructure logs, Grafana Alloy collect and forwards logs.

#### Application Monitoring

A FastAPI demo application exposes application metrics for Prometheus.

### Deployment

Helm manages application and infrastructure configuration. Argo CD Provides GitOps-based deployment.

## Environment

### Local
Kind running on Docker Desktop

### Cloud

Design for migrations to EKS, AKS or GKE.

### Design Principles

- Declarative configuration
- Repoducible deployments
- Least priviledge access
- Separation of concerns
- Persistent storage
- Infrastructure as Code
- GitOps deployment workflows
