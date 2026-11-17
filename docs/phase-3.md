Fase 3 – Centraliseret logging med Loki og Grafana Alloy
Portfolio
Kind
Helm
GitOps-ready

1. Formålet med fasen
Vi skal bygge en komplet logging-platform, hvor logs fra Kubernetes automatisk indsamles, opbevares og kan søges frem i Grafana.

Arkitekturen bliver:
Kubernetes workloads

Monitoring · Logging · Demo-app · System pods

Grafana Alloy

Discovery · Log collection · Labels

Grafana Loki

Log storage · Indexing · Retention

Grafana

Explore · LogQL · Dashboards


Vi bruger følgende komponenter:
Komponent	Funktion
Loki	Opbevarer og indekserer logs
Grafana Alloy	Indsamler og videresender logs
LogQL	Søgesprog til logs
Grafana	Søgeinterface og visualisering
Helm	Installation og konfiguration


Del 1 – Forberedelse
2. Kontrollér cluster og namespaces
Kontrollér først, at du arbejder i det rigtige cluster:
kubectl config current-context


Forventet:
kind-monitoring-platform


Kontrollér noder:
kubectl get nodes


Alle skal være Ready.

Kontrollér namespaces:
kubectl get namespaces


Vi skal bruge:
- monitoring
- logging
- demo-app
Kontrollér også, at Prometheus/Grafana stadig fungerer:
kubectl get pods -n monitoring


3. Tilføj Helm repositories
Loki-chartet vedligeholdes nu i Grafana Community-repository. Alloy-chartet ligger i Grafanas Helm-repository.
Grafana Loki documentation+1


Tilføj repositories:
helm repo add grafana-community https://grafana-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts


Opdatér:
helm repo update


4. Find og fastlås chart-versionerne
Vi vil ikke installere med en flydende version. Vi vælger en konkret chart-version og gemmer den i installationskommandoerne.

Find Loki-versioner:
helm search repo grafana-community/loki --versions | head -10


Find Alloy-versioner:
helm search repo grafana/alloy --versions | head -10


Vælg en stabil version af hvert chart, og notér dem.

I de følgende kommandoer erstatter du X.Y.Z med de valgte versioner.
LOKI_CHART_VERSION="X.Y.Z"
ALLOY_CHART_VERSION="X.Y.Z"


Gem gerne versionerne i din projektdokumentation.

Vigtigt: Community-chart version 12 og nyere bruger Monolithic som betegnelse for Single Binary. Vi bruger den nye betegnelse.
Grafana Loki documentation+1


Del 2 – Loki
5. Undersøg Loki-chartets standardværdier
Før vi skriver vores egen konfiguration, undersøger vi chartets standardværdier.
helm show values grafana-community/loki \
  --version "$LOKI_CHART_VERSION" \
  > /tmp/loki-default-values.yaml


Åbn filen:
less /tmp/loki-default-values.yaml


Her kan du se alle de indstillinger, som chartet understøtter.

Du kan søge i filen med / efter eksempelvis:
- deploymentMode
- singleBinary
- schemaConfig
- storage
- retention
- gateway
Tryk q for at afslutte.
6. Konfigurér Loki
Vi skal nu udfylde:
infrastructure/helm/logging/loki/values.yaml


Erstat indholdet med følgende:

# Deployment mode
# Monolithic runs all Loki components in one process.
deploymentMode: Monolithic

# Loki configuration
loki:
  # Authentication is disabled for this private local lab.
  auth_enabled: false

  # A single replica requires replication factor 1.
  commonConfig:
    replication_factor: 1

  # Storage schema for a new Loki installation.
  schemaConfig:
    configs:
      - from: "2024-04-01"
        store: tsdb
        object_store: filesystem
        schema: v13
        index:
          prefix: loki_index_
          period: 24h

  # Filesystem storage for local Kind environment.
  storage:
    type: filesystem

  storage_config:
    filesystem:
      directory: /var/loki/chunks

  # Log retention and ingestion limits.
  limits_config:
    allow_structured_metadata: true
    retention_period: 168h

  # Compactor manages retention and deletion.
  compactor:
    working_directory: /var/loki/compactor
    retention_enabled: true
    delete_request_store: filesystem

# Single Loki instance.
singleBinary:
  replicas: 1

  persistence:
    enabled: true
    size: 10Gi
    accessModes:
      - ReadWriteOnce

  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

# Enable gateway for internal cluster access.
gateway:
  enabled: true

# Loki Canary continuously tests log ingestion.
lokiCanary:
  enabled: true

# No MinIO required for filesystem storage.
minio:
  enabled: false

# Disable components not used in Monolithic mode.
backend:
  replicas: 0

read:
  replicas: 0

write:
  replicas: 0

ingester:
  replicas: 0

querier:
  replicas: 0

queryFrontend:
  replicas: 0

queryScheduler:
  replicas: 0

distributor:
  replicas: 0

compactor:
  replicas: 0

indexGateway:
  replicas: 0

bloomPlanner:
  replicas: 0

bloomBuilder:
  replicas: 0

bloomGateway:
  replicas: 0



Hvad betyder konfigurationen?
Indstilling	Forklaring
deploymentMode	Bestemmer, hvordan Loki distribueres
replication_factor	Antal kopier af data i ring-konfigurationen
schemaConfig	Bestemmer, hvordan Loki organiserer logdata
object_store	Bestemmer, hvor logdata opbevares
storage.type	Vælger storage-backend
retention_period	Hvor længe logs skal beholdes
compactor	Rydder op i udløbne logs
persistence	Sikrer, at data overlever pod-genstart
resources	Sætter CPU- og memory-grænser
gateway	Giver en fælles intern HTTP-indgang til Loki

168h svarer til 7 dage.

Filesystem-storage er passende til vores lokale installation. Ved cloud-migration skifter vi til objektstorage som S3, GCS eller Azure Blob.
Grafana Loki documentation+2

7. Valider Loki-konfigurationen
Før installation skal vi rendere Helm-manifesterne.
helm template loki grafana-community/loki \
  --version "$LOKI_CHART_VERSION" \
  --namespace logging \
  --values infrastructure/helm/logging/loki/values.yaml \
  > /tmp/loki-rendered.yaml


Kontrollér filens størrelse:
wc -l /tmp/loki-rendered.yaml


Kontrollér vigtige konfigurationsværdier:
grep -nE 'retention_period|replication_factor|filesystem|loki-gateway' /tmp/loki-rendered.yaml


Hvis der er fejl, skal de rettes før installation.
8. Installer Loki
Når renderingen er godkendt:
helm upgrade --install loki grafana-community/loki \
  --version "$LOKI_CHART_VERSION" \
  --namespace logging \
  --values infrastructure/helm/logging/loki/values.yaml \
  --wait \
  --timeout 10m


Dette installerer Loki i logging.
9. Kontrollér Loki-installationen
Kontrollér Helm:
helm list -n logging


Kontrollér pods:
kubectl get pods -n logging -o wide


Kontrollér services:
kubectl get svc -n logging


Kontrollér persistent storage:
kubectl get pvc -n logging


Forventet:
- Loki-pod er Running.
- Loki PVC er Bound.
- Loki Gateway Service eksisterer.
- Loki Canary kører.
Notér det faktiske navn på gateway-servicen. Vi forventer normalt loki-gateway.
10. Test Loki direkte
Vi tester Loki's readiness endpoint, inden Alloy bliver installeret.

Åbn en terminal:
kubectl port-forward svc/loki-gateway 3100:80 -n logging


Lad terminalen stå åben.

Åbn en ny terminal og kør:
curl -i http://localhost:3100/ready


Forventet:
HTTP/1.1 200 OK


Når testen er færdig, kan du stoppe port-forward med Ctrl+C.

Del 3 – Grafana Alloy
11. Undersøg Alloy-chartets standardværdier
Nu undersøger vi Alloy-chartet.
helm show values grafana/alloy \
  --version "$ALLOY_CHART_VERSION" \
  > /tmp/alloy-default-values.yaml


Åbn filen:
less /tmp/alloy-default-values.yaml


Find især:
- controller
- configMap
- serviceAccount
- rbac
- mounts
Alloy har brug for adgang til Kubernetes API'et, så den kan opdage pods og læse deres logs.
12. Konfigurér Alloy
Vi udfylder:
infrastructure/helm/logging/alloy/values.yaml


Erstat indholdet med:

# Run one Alloy instance as a Deployment.
controller:
  type: deployment
  replicas: 1

alloy:
  enableReporting: false

  # Kubernetes API log collection does not require host log mounts.
  mounts:
    varlog: false

  configMap:
    create: true

    content: |-
      logging {
        level  = "info"
        format = "logfmt"
      }

      // Discover Kubernetes pods.
      discovery.kubernetes "pods" {
        role = "pod"
      }

      // Collect logs from discovered pods.
      loki.source.kubernetes "pods" {
        targets = discovery.kubernetes.pods.targets
        forward_to = [loki.write.endpoint.receiver]
      }

      // Forward logs to Loki Gateway.
      loki.write "endpoint" {
        endpoint {
          url = "http://loki-gateway.logging.svc.cluster.local/loki/api/v1/push"
        }
      }



Hvad sker der i Alloy-konfigurationen?
Vi har tre centrale komponenter.

A. discovery.kubernetes
discovery.kubernetes "pods" {
  role = "pod"
}


Alloy spørger Kubernetes API'et efter pods.

Den finder blandt andet:
- Pod-navn
- Namespace
- Container
- Kubernetes metadata
B. loki.source.kubernetes
loki.source.kubernetes "pods" {
  targets = discovery.kubernetes.pods.targets
  forward_to = [loki.write.endpoint.receiver]
}


Denne komponent henter logs fra de pods, der blev opdaget.

C. loki.write
loki.write "endpoint" {
  endpoint {
    url = "http://loki-gateway.logging.svc.cluster.local/loki/api/v1/push"
  }
}


Denne komponent sender logs til Loki.

Her bruger vi Kubernetes DNS:
loki-gateway.logging.svc.cluster.local


Det betyder:
- loki-gateway = Service
- logging = Namespace
- svc = Kubernetes Service
- cluster.local = Cluster-domæne
Adressen virker først, når Loki Gateway Service eksisterer.

Alloys chart har indbygget RBAC-understøttelse til Kubernetes-discovery og logindsamling. Vi bruger chartets standard RBAC-regler her.
GitHub+2

13. Valider Alloy-konfigurationen
Render konfigurationen:
helm template alloy grafana/alloy \
  --version "$ALLOY_CHART_VERSION" \
  --namespace logging \
  --values infrastructure/helm/logging/alloy/values.yaml \
  > /tmp/alloy-rendered.yaml


Kontrollér output:
wc -l /tmp/alloy-rendered.yaml


Kontrollér, at konfigurationen er med:
grep -nE 'loki.write|loki.source.kubernetes|discovery.kubernetes|loki-gateway' /tmp/alloy-rendered.yaml


14. Installer Alloy
Når renderingen er godkendt:
helm upgrade --install alloy grafana/alloy \
  --version "$ALLOY_CHART_VERSION" \
  --namespace logging \
  --values infrastructure/helm/logging/alloy/values.yaml \
  --wait \
  --timeout 10m


15. Kontrollér Alloy
Kontrollér Helm releases:
helm list -n logging


Kontrollér pods:
kubectl get pods -n logging -o wide


Kontrollér Deployment:
kubectl get deployment -n logging


Kontrollér logs:
kubectl logs deployment/alloy -n logging --tail=100


Vi ønsker at se, at Alloy starter uden konfigurationsfejl eller RBAC-fejl.

Del 4 – Test logindsamling
16. Opret en test-applikation, der producerer logs
Nu laver vi en lille testpod, som løbende skriver logs.
kubectl run log-generator \
  --namespace demo-app \
  --image=busybox:1.36 \
  --restart=Never \
  --command -- sh -c 'i=0; while true; do echo "observability-test message=$i"; i=$((i+1)); sleep 5; done'


Kontrollér pod:
kubectl get pods -n demo-app


Se logs:
kubectl logs log-generator -n demo-app --tail=10


Du skal kunne se:
observability-test message=0
observability-test message=1
observability-test message=2


Nu har vi en testkilde, som Alloy kan indsamle logs fra.
17. Kontrollér, at Alloy sender logs til Loki
Kontrollér Alloy-logs:
kubectl logs deployment/alloy -n logging --tail=100


Kontrollér også Loki:
kubectl logs -n logging -l app.kubernetes.io/component=single-binary --tail=100


Vi leder efter fejl om forbindelser, permissions eller log ingestion.

Del 5 – Grafana integration
18. Åbn Grafana
Hvis Grafana-port-forward ikke allerede kører:
kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring


Åbn:
Grafana19. Tilføj Loki som Data Source
I Grafana:
1. Gå til Connections.
2. Vælg Data sources.
3. Klik Add data source.
4. Vælg Loki.
5.
grafana.com

Indtast under HTTP URL:
http://loki-gateway.logging.svc.cluster.local


Klik:

Save & test

Forventet resultat: Grafana kan kontakte Loki.

Bemærk, at dette er Grafanas query-adresse. Alloy bruger samme Gateway, men tilføjer /loki/api/v1/push for at sende logs.
1.  Test logs i Grafana Explore
Gå til:

Explore → Loki

Indtast følgende LogQL:
{namespace="demo-app"}


Klik Run query.

Du skulle gerne kunne finde logs fra vores log-generator.








programmingwithwolfgang.com


Prøv derefter:

Filtrér på pod:
{namespace="demo-app", pod="log-generator"}


Find logs med et bestemt ord:
{namespace="demo-app"} |= "observability-test"


Find fejlmeddelelser:
{namespace="monitoring"} |= "error"


Vis antal logs over de sidste fem minutter:
count_over_time({namespace="demo-app"}[5m])


Det sidste eksempel viser, hvordan LogQL også kan bruges til at beregne logvolumen.
21. Opret et Grafana dashboard
Nu hvor logs virker, kan du oprette et dashboard.

Gå til:

Dashboards → New → New dashboard

Tilføj en visualisering med Loki som Data Source.

Brug eksempelvis:
count_over_time({namespace="demo-app"}[5m])


Giv dashboardet navnet:

Kubernetes Application Logs

Tilføj gerne et panel med:
{namespace="demo-app"}


Så har du både en logvisning og en graf over logaktivitet.

Del 6 – Dokumentation og oprydning
22. Fjern testpodden
Når du har verificeret logindsamlingen:
kubectl delete pod log-generator -n demo-app


Det fjerner kun vores midlertidige testpod. Loki's PVC og indsamlede logdata bliver ikke slettet.
23. Dokumentér installationen
Opret:
touch docs/phase-3-logging.md


Indsæt:
Phase 3 – Centralized Logging
Overview
This phase implements centralized Kubernetes logging using Grafana Loki and Grafana Alloy.
Architecture
Kubernetes Pods → Grafana Alloy → Loki → Grafana
Components
Loki
- Monolithic deployment
- Filesystem storage
- Persistent Volume Claim
- Seven-day log retention
- Helm-managed configuration
Grafana Alloy
- Kubernetes pod discovery
- Kubernetes API-based log collection
- Log forwarding to Loki
- Helm-managed configuration
Grafana
- Loki data source
- Explore and LogQL
- Kubernetes application log dashboard
Validation
- Loki pod is Running
- Loki PVC is Bound
- Loki Gateway is available
- Alloy Deployment is Running
- Alloy can discover Kubernetes pods
- Logs are visible in Grafana Explore
- LogQL queries return results
Cloud Migration
The local filesystem storage configuration is intended for Kind development.

For cloud deployment, evaluate managed object storage such as Amazon S3, Google Cloud Storage, or Azure Blob Storage.
Status
Development in progress.




24. Git commit
Kontrollér først dine filer:
git status


Tilføj konfigurationen:
git add infrastructure/helm/logging docs/phase-3-logging.md


Commit:
git commit -m "Add Loki and Grafana Alloy centralized logging"


Husk, at vi ikke lægger credentials eller private nøgler i repository'et.

Definition of Done – Fase 3
Fase 3 – Progress
0/15



[ ] Loki chart-version er fastlåst
[ ] Loki values.yaml er konfigureret
[ ] Loki Helm rendering gennemføres uden fejl
[ ] Loki er installeret og pod er Running
[ ] Loki PVC er Bound
[ ] Loki Gateway er tilgængelig
[ ] Alloy chart-version er fastlåst
[ ] Alloy values.yaml er konfigureret
[ ] Alloy Helm rendering gennemføres uden fejl
[ ] Alloy Deployment er Running
[ ] Alloy kan læse Kubernetes pod logs
[ ] Grafana Loki Data Source er Connected
[ ] LogQL returnerer logs fra demo-app
[ ] Grafana dashboard er oprettet
[ ] Dokumentation og Git commit er gennemført

Vigtig læring: Local kontra Cloud
Område	Lokal Kind	Cloud
Loki deployment	Monolithic	Kan skaleres
Storage	Filesystem + PVC	S3/GCS/Azure Blob
Alloy	Deployment	Deployment eller DaemonSet afhængigt af indsamlingsmetode
Grafana	Lokal Kubernetes-service	Managed eller selvhostet
Retention	7 dage	Tilpasses behov og omkostninger

Vi har bevidst valgt en enkel lokal arkitektur, men konfigurationen er struktureret, så vi senere kan udskifte storage-backend og udvide Loki.

En vigtig produktionsbemærkning: Vores nuværende Loki-installation har ikke HA og er ikke en produktionsklar cloud-konfiguration. Den er et lokalt udviklingsmiljø med persistent storage. Cloud-delen skal have objektstorage, passende adgangskontrol, backups og en skaleringsstrategi.

Officiel dokumentation
Her er de dokumenter, jeg anbefaler, at du bruger som opslagsværker, mens du arbejder:
- Grafana Loki – Helm installation
- Loki Helm values reference
- Grafana Alloy documentation
- Collect Kubernetes logs with Alloy
- LogQL documentation