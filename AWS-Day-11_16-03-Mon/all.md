# 📓 Daily Practice log
**Date:** 2026-03-16
**Focus:** Docker → ECR → ECS → EKS → AWS Databases → Full Containerized App Deployment

---

## 📚 Topics Covered

---

### 🐳 Docker — Complete Reference from Official Docs

Docker is an open platform for developing, shipping, and running applications inside **containers** — isolated environments that package code and all its dependencies.

#### Core Concepts
| Concept | Description |
|---|---|
| **Image** | Read-only template used to create containers. Built from a `Dockerfile`. |
| **Container** | Runnable instance of an image. Isolated process on the host OS. |
| **Dockerfile** | Text file with instructions to assemble an image. |
| **Registry** | Storage and distribution system for images (e.g., Docker Hub, ECR). |
| **Volume** | Persistent data storage that survives container restarts. |
| **Network** | Virtual network that allows containers to communicate. |
| **Docker Engine** | Client-server app: daemon (`dockerd`), REST API, CLI (`docker`). |
| **Docker Compose** | Tool for defining and running multi-container apps via `docker-compose.yml`. |

#### Essential Commands
```bash
# --- Images ---
docker build -t <name>:<tag> .          # Build image from Dockerfile in current dir
docker images                            # List local images
docker pull <image>                      # Pull image from registry
docker push <image>                      # Push image to registry
docker rmi <image>                       # Remove image
docker tag <src> <target>                # Tag an image with a new name

# --- Containers ---
docker run -d -p 80:80 --name myapp nginx   # Run container detached, map ports
docker run -it ubuntu bash                   # Run interactively
docker ps                                    # List running containers
docker ps -a                                 # List all containers (including stopped)
docker stop <container>                      # Gracefully stop container
docker start <container>                     # Start stopped container
docker rm <container>                        # Remove container
docker exec -it <container> bash             # Shell into running container
docker logs <container>                      # View container stdout/stderr
docker inspect <container>                   # Low-level details (JSON)

# --- Volumes ---
docker volume create myvol
docker run -v myvol:/app/data nginx
docker volume ls
docker volume rm myvol

# --- Networks ---
docker network create mynet
docker run --network mynet nginx
docker network ls

# --- System Cleanup ---
docker system prune -a                   # Remove all unused images, containers, volumes
docker image prune                       # Remove dangling images only

# --- Docker Compose ---
docker compose up -d                     # Start all services in background
docker compose down                      # Stop and remove containers
docker compose logs -f                   # Follow logs
docker compose ps                        # List running services
```

#### Dockerfile — Key Instructions
```dockerfile
FROM python:3.11-slim          # Base image
WORKDIR /app                   # Set working directory
COPY requirements.txt .        # Copy files
RUN pip install -r requirements.txt   # Execute command at build time
ENV PORT=5000                  # Set environment variable
EXPOSE 5000                    # Document which port the container listens on
CMD ["gunicorn", "app:app"]    # Default command when container starts
ENTRYPOINT ["python"]          # Fixed executable (CMD appended as args)
ARG BUILD_VERSION              # Build-time variable (not in final image)
VOLUME ["/data"]               # Declare mount point
HEALTHCHECK CMD curl -f http://localhost/ || exit 1
```

> **Best practices:** Use slim/alpine base images, combine RUN commands to reduce layers, use `.dockerignore`, never store secrets in images, run as non-root user.

---

### 🐳 Docker Hub

- **What it is:** Docker's official cloud-based registry for storing and sharing container images.
- **Free tier:** Unlimited public repos, 1 private repo.
- **Official Images:** Curated images for popular software (nginx, postgres, python, etc.).
- **Verified Publishers:** Images from trusted ISVs.

```bash
docker login                              # Login to Docker Hub
docker tag myapp:latest username/myapp:v1
docker push username/myapp:v1             # Push to Docker Hub
docker pull username/myapp:v1             # Pull from Docker Hub
```

---

### 🖥️ Docker Desktop

- GUI application for Mac/Windows (and Linux) that bundles Docker Engine, Docker CLI, Docker Compose, and Kubernetes.
- Provides a visual dashboard to manage containers, images, volumes, and networks.
- Includes Dev Environments, Docker Extensions marketplace.
- **WSL 2 integration** on Windows — runs Docker natively in WSL2 Linux kernel.

---

### 📦 AWS ECR (Elastic Container Registry)

- **What it is:** AWS-managed, private Docker container registry — fully integrated with IAM, ECS, EKS, and CodePipeline.
- **Types:** Private registries (per AWS account) and Public registries (ECR Public / gallery.ecr.aws).
- **Features:** Image scanning (basic + enhanced via Inspector), lifecycle policies, cross-region replication, immutable image tags.

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region <region> | \
  docker login --username AWS --password-stdin \
  <account_id>.dkr.ecr.<region>.amazonaws.com

# Create repository
aws ecr create-repository --repository-name myapp --region <region>

# Tag & push
docker tag myapp:latest <account_id>.dkr.ecr.<region>.amazonaws.com/myapp:latest
docker push <account_id>.dkr.ecr.<region>.amazonaws.com/myapp:latest

# List images
aws ecr list-images --repository-name myapp

# Enable image scanning on push
aws ecr put-image-scanning-configuration \
  --repository-name myapp \
  --image-scanning-configuration scanOnPush=true
```

---

### ⚙️ AWS ECS (Elastic Container Service)

- **What it is:** AWS-managed container orchestration service. Run and scale containerized apps without managing Kubernetes control plane.
- **Key components:**
  - **Cluster** — Logical grouping of tasks/services and infrastructure.
  - **Task Definition** — Blueprint (JSON) specifying containers, CPU, memory, networking, IAM roles, volumes.
  - **Task** — Running instantiation of a task definition (one-shot or part of a service).
  - **Service** — Ensures a desired number of task replicas are always running; integrates with ALB.
  - **Container Agent** — Runs on EC2 nodes and communicates with ECS control plane.
- **Launch types:** Fargate (serverless) or EC2 (self-managed nodes).

---

### ☁️ AWS Fargate

- **What it is:** Serverless compute engine for containers. Works with ECS and EKS.
- You define CPU/memory at task level. AWS provisions, scales, and manages the underlying instances.
- **No** cluster node management, patching, or capacity planning.
- **Billing:** Per vCPU and memory per second of task runtime.
- **Use when:** You want zero infrastructure management, variable workloads, or fast auto-scaling.

---

### 🔀 ECS with Fargate vs ECS with EC2

| Feature | ECS + Fargate | ECS + EC2 |
|---|---|---|
| Infrastructure management | None (serverless) | You manage EC2 nodes |
| Pricing model | Per task CPU/memory/second | Per EC2 instance hour |
| Cost efficiency | Higher per-unit cost, less ops overhead | Cheaper at scale with Reserved/Spot |
| GPU support | No | Yes |
| Custom AMI / kernel | No | Yes |
| Startup time | Slightly slower (cold start) | Faster (pre-warmed nodes) |
| Visibility into host | No | Yes (SSH, CloudWatch agent) |
| Best for | Small-medium workloads, variable traffic | Large steady-state workloads, GPU, custom tuning |

---

### ☸️ Amazon EKS (Elastic Kubernetes Service)

- **What it is:** AWS-managed Kubernetes control plane. AWS runs and scales the Kubernetes API server and etcd. You manage worker nodes (EC2, Fargate, or Karpenter).
- **Why EKS over ECS?**
  - Kubernetes is the industry standard — portable across clouds.
  - Richer ecosystem: Helm, Istio, Prometheus, ArgoCD, etc.
  - Multi-cloud / hybrid-cloud scenarios.
  - More control over networking (CNI), scheduling, and autoscaling.
- **Node options:** Managed Node Groups, Self-managed EC2, Fargate profiles, Karpenter.
- **Key tools:** `kubectl` (Kubernetes CLI), `eksctl` (EKS cluster management CLI).

```bash
# Create cluster
eksctl create cluster --name mycluster --region ap-south-1 --node-type t3.small

# Get kubeconfig
aws eks update-kubeconfig --name mycluster --region ap-south-1

# Basic kubectl
kubectl get nodes
kubectl get pods -A
kubectl apply -f deployment.yaml
kubectl get svc
kubectl describe pod <name>
kubectl logs <pod>
kubectl delete -f deployment.yaml

# Secrets
kubectl create secret generic rds-secret \
  --from-literal=MYSQL_USER=admin \
  --from-literal=MYSQL_PASSWORD=secret \
  --from-literal=MYSQL_HOST=db.rds.amazonaws.com \
  --from-literal=MYSQL_DB=test
```

---

### 📊 ECR vs Docker Hub

| Feature | AWS ECR | Docker Hub |
|---|---|---|
| Hosting | AWS-managed, private | Cloud (public or private) |
| IAM integration | Native AWS IAM | No |
| Network | Private VPC endpoint available | Public internet |
| Image scanning | Built-in (Inspector) | Paid tiers |
| Lifecycle policies | Yes | Limited |
| Free tier | 500 MB/month (private) | 1 free private repo |
| Best for | AWS-native deployments | Public open-source images |

---

### 🗄️ AWS Databases — All Types

| Service | Type | Use Case |
|---|---|---|
| **RDS** | Managed relational (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server, Db2) | Traditional web apps, transactional workloads |
| **Aurora** | Cloud-native relational (MySQL/PostgreSQL-compatible) | High performance, auto-scaling storage, multi-AZ |
| **Aurora Serverless v2** | Auto-scales Aurora capacity | Variable/unpredictable workloads |
| **DynamoDB** | Managed NoSQL key-value + document | Millisecond latency at any scale, IoT, gaming |
| **ElastiCache** | In-memory (Redis, Memcached) | Caching, session store, leaderboards |
| **MemoryDB for Redis** | Durable in-memory Redis | Redis as primary database |
| **DocumentDB** | MongoDB-compatible managed document DB | JSON documents, content management |
| **Keyspaces** | Apache Cassandra-compatible | Wide-column, time-series, IoT at scale |
| **Neptune** | Managed graph database | Social networks, fraud detection, knowledge graphs |
| **Timestream** | Serverless time-series | IoT metrics, DevOps telemetry |
| **QLDB** | Serverless ledger database | Immutable, cryptographically verifiable records |
| **Redshift** | Managed data warehouse | OLAP, analytics, petabyte-scale SQL queries |
| **OpenSearch Service** | Search & analytics (Elasticsearch-compatible) | Log analytics, full-text search |

---

### ❓ Why ECS + Fargate Instead of Plain EC2?

| Concern | EC2 (bare) | ECS + Fargate |
|---|---|---|
| Provisioning | Manual | Automatic |
| Patching OS | You | AWS |
| Scaling containers | Manual or custom scripts | Built-in service auto-scaling |
| Load balancer integration | Manual ALB config | Native ECS integration |
| Health replacement | Manual | Automatic task replacement |
| Cost granularity | Per instance hour | Per second of task runtime |
| Security isolation | Shared host | Task-level IAM + network isolation |

> **Bottom line:** EC2 is infrastructure. ECS+Fargate is a platform. Fargate removes the undifferentiated heavy lifting of managing servers so you focus purely on your application.

---

## ✅ Tasks Completed

---

### Task 1 — Build & Push Docker Image to ECR ✅

**Goal:** Containerize the Mario game app and push to AWS ECR.

**Steps done:**
```bash
# 1. Source code cloned from GitHub
git clone https://github.com/Fardeen313/Maven_Mario_Raw_Code.git

# 2. Build Docker image locally (WSL)
docker build -t mariogame .

# 3. Authenticate to ECR (eu-north-1)
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  863942760608.dkr.ecr.eu-north-1.amazonaws.com

# 4. Tag image with ECR URI
docker tag mariogame:latest \
  863942760860.dkr.ecr.eu-north-1.amazonaws.com/mariogame:latest

# 5. Push to ECR
docker push 863942760608.dkr.ecr.eu-north-1.amazonaws.com/mariogame:latest
```

**Proof:**
- GitHub Repo: https://github.com/Fardeen313/Maven_Mario_Raw_Code.git
- ECR Repository: `mariogame` in region `eu-north-1`
- Image URI: `863942760608.dkr.ecr.eu-north-1.amazonaws.com/mariogame:latest`

---

### Task 2 — Deploy App on ECS ✅

**Goal:** Run the containerized Mario game on AWS ECS using Fargate.

**Steps done:**
1. Created **Task Definition** pointing to ECR image URI.
2. Created **ECS Cluster**.
3. Created **ECS Service** from task definition.
4. Attached **Application Load Balancer (ALB)** and **Target Group** to the service.
5. Service maintains desired count of tasks; ALB distributes traffic.

**Architecture:**
```
Internet → ALB → Target Group → ECS Service → Task (mariogame container from ECR)
```

---

### Task 3 — Deploy App on EKS ✅

**Goal:** Run a containerized app on Amazon EKS.

**EC2 setup & tool installation:**
```bash
# kubectl
curl -o kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.19.6/2021-01-05/bin/linux/amd64/kubectl
chmod +x ./kubectl
mv ./kubectl /usr/local/bin
kubectl version --short --client

# eksctl
curl --silent --location \
  "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" \
  | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

**Cluster creation:**
```bash
eksctl create cluster \
  --name webgame \
  --region ap-south-1 \
  --node-type t3.small
```
**kubectl apply -f deployment.yaml**

**kubectl apply -f service.yaml**
---

### Task 4 — Database Integration with EKS (Flask App) ✅

**Goal:** Deploy a Python Flask app on EKS connected to AWS RDS MySQL, with a browser-based CRUD dashboard.

#### Application Stack
| Layer | Technology |
|---|---|
| Backend | Python Flask + SQLAlchemy |
| Database | AWS RDS MySQL (`database-1.cglioew4ktr8.us-east-1.rds.amazonaws.com`) |
| Container | Docker (`python:3.11-slim` + gunicorn) |
| Registry | Docker Hub — `fardeenattar/flaskapp:v2` |
| Orchestration | Amazon EKS |
| Secrets | Kubernetes Secret (`rds-secret`) |

#### Source Files

**`requirements.txt`**
```
flask
flask-sqlalchemy
pymysql
cryptography
python-dotenv
gunicorn
```

**`Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y \
    gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```
**Built and pushed image to dockerhub registry https://hub.docker.com/r/fardeenattar/flaskapp/tags**

#### Kubernetes Manifests

**`secret.yml`** — RDS credentials as K8s Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rds-secret
type: Opaque
stringData:
  MYSQL_USER: "admin"
  MYSQL_PASSWORD: "dbpasswd"
  MYSQL_HOST: "database-1.cglioew4ktr8.us-east-1.rds.amazonaws.com"
  MYSQL_DB: "test"
```

**`flask-deployment.yaml`** — Deployment + LoadBalancer Service
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask-app
  template:
    metadata:
      labels:
        app: flask-app
    spec:
      containers:
        - name: flask-app
          image: fardeenattar/flaskapp:v2
          ports:
            - containerPort: 5000
          env:
            - name: MYSQL_USER
              valueFrom:
                secretKeyRef:
                  name: rds-secret
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: rds-secret
                  key: MYSQL_PASSWORD
            - name: MYSQL_HOST
              valueFrom:
                secretKeyRef:
                  name: rds-secret
                  key: MYSQL_HOST
            - name: MYSQL_PORT
              value: "3306"
            - name: MYSQL_DB
              valueFrom:
                secretKeyRef:
                  name: rds-secret
                  key: MYSQL_DB
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 15
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 30
            periodSeconds: 15
---
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask-app
  type: LoadBalancer
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
```

#### Deployment Commands
```bash
# Apply secret first
kubectl apply -f secret.yml

# Deploy app
kubectl apply -f flask-deployment.yaml

# Verify pods
kubectl get pods
kubectl get svc flask-service

# Get external LoadBalancer URL
kubectl get svc flask-service -o wide
```

#### Database Seed (test.sql)
```sql
USE test;
SHOW TABLES;   -- Verify Flask created the users table

INSERT INTO users (name, email) VALUES
  ('Fardeena Attar',  'fardeen@example.com'),
  ('John Smith',      'john.smith@example.com'),
  ('Priya Sharma',    'priya.sharma@example.com'),
  ('Mohammed Ali',    'mohammed.ali@example.com'),
  ('Sarah Johnson',   'sarah.johnson@example.com');

SELECT * FROM users;
```

#### API Endpoints Summary
| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | HTML dashboard |
| GET | `/health` | API + DB health check |
| POST | `/users` | Create user `{name, email}` |
| GET | `/users` | List all users |
| GET | `/users/<id>` | Get user by ID |
| PUT | `/users/<id>` | Update user name/email |
| DELETE | `/users/<id>` | Delete user |

#### Architecture Diagram
```
Browser
  │
  ▼
K8s LoadBalancer Service (port 80)
  │
  ▼
Flask Pod 1 ──┐
              ├──► AWS RDS MySQL (port 3306)
Flask Pod 2 ──┘
  │
  └── Credentials from K8s Secret (rds-secret)
```

**Proof:**
- Docker Hub Image: `fardeenattar/flaskapp:v2`
- EKS Cluster: `webgame` (ap-south-1)
- RDS: `database-1.cglioew4ktr8.us-east-1.rds.amazonaws.com`
- Replicas: 2 pods with readiness + liveness probes
- Security: DB credentials injected via K8s Secrets (not hardcoded in image)

---

## 🔐 Security Best Practices Applied

| Practice | Where Applied |
|---|---|
| No credentials in Docker image | Env vars via K8s Secrets |
| `NoEcho: true` on CFT passwords | CloudFormation template |
| RDS not publicly accessible | VPC security group (port 3306 internal only) |
| Container runs as non-root | `python:3.11-slim` default |
| Image scanning on push | ECR scan-on-push enabled |
| Health probes | Readiness + liveness on `/health` |
| Connection pooling | `pool_pre_ping`, `pool_recycle` in SQLAlchemy |
| Duplicate email check | 409 conflict response in Flask |

---

