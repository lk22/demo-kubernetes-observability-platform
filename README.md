# Kubernetes Observability Platform

A cloud-ready Kubernetes observability platform built with open-source cloud-native technologies.

## Project Overview

This project demonstrates how to build, deploy, secure, and operate a modern observability platform on Kubernetes.

The platform provides centralized metrics, logging, visualization, and alerting across Kubernetes workloads.

## Technology Stack

- Kubernetes (Kind locally)
- Helm
- Prometheus
- Grafana
- Alertmanager
- Node Exporter
- kube-state-metrics
- Loki
- Grafana Alloy
- FastAPI
- Argo CD
- GitHub Actions
- Trivy
- Cosign
- Kyverno

## Architecture

The platform is designed to run locally on Kind and is structured for future deployment to managed Kubernetes services such as Amazon EKS, Azure AKS, and Google GKE.

## Project Goals

- Centralized Kubernetes monitoring
- Metrics collection and visualization
- Centralized application logging
- Alerting and operational visibility
- Secure container image delivery
- GitOps-based deployment
- Infrastructure as Code
- Cloud-ready architecture

## Project Structure

- `applications/` – Demo applications
- `infrastructure/` – Kubernetes and Helm configuration
- `dashboards/` – Grafana dashboards
- `alerts/` – Alerting rules
- `.github/workflows/` – CI/CD pipelines
- `docs/` – Architecture and operational documentation

## Status

Development in progress.