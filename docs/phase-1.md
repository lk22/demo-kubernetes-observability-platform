# Phase one

## initial steps
make sure you have helm installed

create helm values configuration file values.yaml in /infrastructure/helm/monitoring/values.yaml

what it could look like
```yaml

# Prometheus configuration
prometheus:
  enabled: true
  prometheusSpec:
    retention: 7d
    replicas: 1
    resources:
      requests:
        cpu: 200m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 2Gi

# Grafana configuration
grafana:
  enabled: true
  adminPassword: "CHANGE_ME"
  persistence:
    enabled: true
    type: pvc
    size: 5Gi
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

# Alertmanager configuration
alertmanager:
  enabled: true
  alertmanagerSpec:
    retention: 120h
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi

# Kubernetes monitoring components
nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true
```

make sure to lint your values file
if you have a Chart.yaml
you can run following command
```bash
helm lint infrastructure/helm/monitoring \
  --values infrastructure/helm/monitoring/values.yaml \
  --strict
```

otherwise we can validate and save the config up agains prometheus's own template configuration file by running following command
this will save and run the configuration from a temp configuration file you have saved.

We do this to control that helm can translate the values for valid kubernetes resourves before the get installed
```bash
helm template monitoring prometheus-community/kube-prometheus-stack \
  --version 93.3.1 \
  --namespace monitoring \
  --values infrastructure/helm/monitoring/values.yaml \
  > /tmp/monitoring-rendered.yaml
```


## 1. Project architecture

| Component | Function |
---------------------------
| Kubernetes | Container orchestration |
| Helm | Installation and configuration
| Prometheus | Metrics collection |
| Grafana | Dashboard and visualization |
| Alertmanager | Alarms |
| Node Exporter | Node metrics |
| kube-state-metrics | Kubernetes resource metrics |
| Loki | Centralized logging |
| Grafana Alloy | Log and telemetry collection |
| FastAPI | Demo application |
| Argo CD | GitOps |
| Github Actions | CI/CD |
| Trivy | Vulnerability scanning |
| Cosign | Image signing |
| Kyberno | Policy enforcement |

## 2 Cluster control
Create the cluster
```bash
kind create cluser --name <cluster-name>
```


make sure you are on the right cluster

```bash
kubectl config current-context
```

this shows the created cluster

control the nodes
```bash
kubectl get nodes -o wide
```
make sure the nodes have following status: Ready

## 3. tool controlling
make sure you have following tools installed

- kubectl
- Helm
- Docker
- Git

```bash
kubectl version --client
helm version
docker --version
git --version
```

## 4. create Project folder structure

kubernetes-observability-platform/
│
├── applications/
│   └── demo-application/
│       ├── app/
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── infrastructure/
│   ├── helm/
│   │   ├── monitoring/
│   │   └── demo-application/
│   │
│   ├── argocd/
│   │
│   └── kubernetes/
│       ├── namespaces/
│       ├── networking/
│       └── security/
│
├── dashboards/
│
├── alerts/
│
├── .github/
│   └── workflows/
│
└── docs/
    ├── architecture.md
    ├── installation.md
    ├── troubleshooting.md
    └── cloud-migration.md


## 5. create cluster namespaces

We need to split up the cluster in namespaces for each part of the architecture

we need one namespace for monitoring purposes
and a namespace for logging purposes
and a final namespace for the application itself

create it by running following commands
```bash
kubectl create namespace monitoring
kubectl create namespace logging
kubectl create namespace <app-name>
```
## 6 setup your gitignore file
example file
cat <<'EOF' > .gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/

# Environment and secrets
.env
.env.*
!.env.example
*.pem
*.key

# Kubernetes
kubeconfig
*.kubeconfig

# macOS
.DS_Store

# Temporary files
*.log
tmp/
EOF

## 7 Add your readme
add your project readme

## 8, 9 and 10
initialize git for your project and commit your project
