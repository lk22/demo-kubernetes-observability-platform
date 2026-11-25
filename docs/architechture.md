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

### GitOps

We are implementing Argo CD for GitOps and verison and installation method

Creating new namespace for all Argo CD resources
```bash
kubectl create namespace argocd
kubectl create namespace gitops-test-namespace <- making sure u either have a test namespace for your deployment or using another namespace for your deployments to be apllied to
```
to apply the argo CD manifests we are apply them from following url https://raw.githubusercontent.com/argoproj/argo-cd/v3.6.1/manifests/install.yaml

```bash
kubectl apply --force-conflicts -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.6.1/manifests/install.yaml
```

this installs all the resources into our cluster on the argo cd namespace.

To access Argo CD web interface run following command
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

if it dont work properly in your browser, your can trustly just open it insecurely

to authenticate properly
use admin as username
and get the password from the secret manifest by running following command

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
echo
```

this echoes out the base64 decoded password from the secret manifest inside the argo CD resources in your cluster

### Troubleshooting

| Argo CD pods dont start | kubectl describe pods -n argocd |
| Application cannot read github | Control the repo URL branch and repo visibility status (needs to be public) |
| Application status is OutOfSync | See ressources and errors in Argo CD |
| Deployment dont starts | kubectl describe deployment <deployment-name> -n <gitops-namespace> |
| Pod is not ready | kubectl logs deployment/<deployment-name> -n <gitops-namespace>
| Self healing is not happening | Control that selfHeal: true in the application manifest sync policy |
| Application shows PermissionDenied | Controll the AppProject manifest, source, destination and resource allowlist |
