# EC2 Advanced Configuration, Hibernation, Placement Groups, and Application Load Balancer with Custom Domain

---

## Table of Contents

1. [EC2 Hibernation](#ec2-hibernation)
2. [Placement Groups](#placement-groups)
3. [Application Load Balancer with Custom Domain & SSL](#application-load-balancer-with-custom-domain--ssl)
4. [Task Completed Summary](#task-completed-summary)

---

## EC2 Hibernation

### What is Hibernation?

EC2 Hibernation saves the **in-memory (RAM) state** of an instance to the root EBS volume and then stops the instance. When started again, the instance resumes exactly where it left off — processes, open files, and running applications are all restored.

### How it works

```
Running Instance (RAM: 4GB used)
        ↓  Hibernate
RAM state → saved to EBS root volume (encrypted)
Instance stops (billing pauses)
        ↓  Start
RAM state → restored from EBS
Instance resumes (uptime continues from before)
```

### Requirements for Hibernation

| Requirement | Details |
|---|---|
| Root Volume | Must be EBS (not instance store) |
| Encryption | Root EBS volume must be encrypted |
| RAM | Instance RAM must be less than 150 GB |
| OS | Amazon Linux 2, Ubuntu, Windows |
| Instance Family | Not supported on bare metal instances |
| Uptime limit | Max 60 days in hibernated state |

### How to Enable Hibernation

When launching an EC2 instance:
> EC2 → Launch Instance → Advanced Details → **Enable Hibernation = Yes**

### Lab Performed: Hibernation with Uptime Check

**Step 1 — Write uptime to /tmp before hibernating:**
```bash
uptime > /tmp/uptime_before.txt
cat /tmp/uptime_before.txt
# Example output: 10:23:01 up 2:14, 1 user, load average: 0.00, 0.00, 0.00
```

**Step 2 — Hibernate the instance:**
> EC2 Console → Select Instance → Instance State → **Hibernate**

**Step 3 — Start the instance again and check uptime:**
```bash
cat /tmp/uptime_before.txt   # File persists from before hibernation
uptime                        # Uptime continues from where it left off
```

**Key Observation:** The `/tmp` directory contents **persisted** after hibernation because RAM state was saved to EBS. The uptime counter also **continued** from where it was before hibernation — unlike a stop/start which resets uptime.

### Hibernation vs Stop vs Reboot

| Action | RAM State | /tmp files | Uptime | Billing |
|---|---|---|---|---|
| Reboot | Cleared | Cleared | Resets | Continuous |
| Stop | Cleared | Cleared | Resets | Paused |
| **Hibernate** | **Saved to EBS** | **Persisted** | **Continues** | **Paused** |

---

## Placement Groups

### What are Placement Groups?

Placement Groups control **how EC2 instances are physically placed** on underlying hardware in AWS data centers. They influence latency, availability, and fault tolerance.

### Types of Placement Groups

#### 1. Cluster Placement Group
```
┌─────────────────────────┐
│   Single AZ             │
│  ┌────┐ ┌────┐ ┌────┐  │
│  │EC2 │─│EC2 │─│EC2 │  │
│  └────┘ └────┘ └────┘  │
│   Low latency network   │
└─────────────────────────┘
```
- All instances in the **same rack / same AZ**
- Extremely **low latency**, high throughput (10 Gbps+)
- **Risk:** If rack fails, all instances fail
- **Use case:** HPC, big data, machine learning training

#### 2. Spread Placement Group
```
AZ-1        AZ-2        AZ-3
┌────┐      ┌────┐      ┌────┐
│EC2 │      │EC2 │      │EC2 │
│Rack1│     │Rack2│     │Rack3│
└────┘      └────┘      └────┘
```
- Instances spread across **distinct hardware racks**
- Max **7 instances per AZ**
- **Use case:** Critical apps needing high availability, small deployments

#### 3. Partition Placement Group
```
Partition 1    Partition 2    Partition 3
┌──────────┐  ┌──────────┐  ┌──────────┐
│ EC2 EC2  │  │ EC2 EC2  │  │ EC2 EC2  │
│ EC2 EC2  │  │ EC2 EC2  │  │ EC2 EC2  │
│  Rack A  │  │  Rack B  │  │  Rack C  │
└──────────┘  └──────────┘  └──────────┘
```
- Instances divided into logical **partitions**, each on separate racks
- Up to **7 partitions per AZ**, hundreds of instances per partition
- **Use case:** Hadoop, Kafka, Cassandra — distributed big data workloads

### Comparison Table

| Feature | Cluster | Spread | Partition |
|---|---|---|---|
| Low latency | ✅ Best | ❌ No | ❌ No |
| High availability | ❌ No | ✅ Best | ✅ Good |
| Max instances | No limit | 7 per AZ | 100s per partition |
| Multi-AZ | ❌ No | ✅ Yes | ✅ Yes |
| Use case | HPC / ML | Critical apps | Big data |

---

## Application Load Balancer with Custom Domain & SSL

### Architecture Overview

```
Internet
    │
    ▼
Route 53 (DNS) ── custom domain ──→ ALB (HTTPS :443)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                    Private EC2 Instance 1   Private EC2 Instance 2
                    (Web App - Private Subnet) (Web App - Private Subnet)
```

### Components Used

| Component | Purpose |
|---|---|
| Route 53 Hosted Zone | DNS management for custom domain |
| ACM Certificate | SSL/TLS certificate for HTTPS |
| Application Load Balancer | Distribute traffic to private instances |
| Target Group | Group of EC2 instances behind ALB |
| Security Groups | Control traffic between ALB and EC2 |

---

### Step 1: Create Hosted Zone in Route 53

> Route 53 → Hosted Zones → Create Hosted Zone

- **Domain name:** `yourdomain.com`
- **Type:** Public Hosted Zone
- After creation, note the **4 NS records** — update these at your domain registrar

---

### Step 2: Request SSL/TLS Certificate from ACM

> ACM (Certificate Manager) → Request Certificate → Public Certificate

- **Domain:** `yourdomain.com` and `*.yourdomain.com` (wildcard)
- **Validation method:** DNS validation (recommended)
- After requesting, ACM provides a **CNAME record** to add to Route 53

**Create DNS validation record:**
> ACM → Certificate → Click "Create records in Route 53" (auto-creates CNAME)

Wait for status to change from **Pending** → **Issued** ✅

---

### Step 3: Create Private EC2 Instances (Web App)

- Launch EC2 instances in **private subnets**
- Install and configure web application (nginx/apache)
- Assign a **Security Group** that allows HTTP (port 80) **only from ALB Security Group**

```
ALB Security Group: Allow 443 from 0.0.0.0/0
EC2 Security Group: Allow 80 from ALB-SG only
```

---

### Step 4: Create Target Group

> EC2 → Target Groups → Create Target Group

| Setting | Value |
|---|---|
| Target type | Instances |
| Protocol | HTTP |
| Port | 80 |
| Health check path | `/` |

- Register private EC2 instances to the target group
- Wait for health checks to show **Healthy** ✅

---

### Step 5: Create Application Load Balancer

> EC2 → Load Balancers → Create → Application Load Balancer

| Setting | Value |
|---|---|
| Scheme | Internet-facing |
| IP address type | IPv4 |
| Subnets | Public subnets (min 2 AZs) |
| Security Group | ALB-SG (allows 443 inbound) |

**Add Listeners:**

| Listener | Protocol | Port | Action |
|---|---|---|---|
| HTTP | HTTP | 80 | Redirect to HTTPS |
| HTTPS | HTTPS | 443 | Forward to Target Group |

**Attach SSL Certificate:**
> HTTPS Listener → Select ACM certificate issued in Step 2

---

### Step 6: Create DNS Record in Route 53

> Route 53 → Hosted Zone → Create Record

| Setting | Value |
|---|---|
| Record name | `www` or `@` (root) |
| Record type | A |
| Alias | Yes |
| Route traffic to | ALB DNS name |

---

### Result

- ✅ Hosted zone created in Route 53
- ✅ SSL/TLS certificate issued by ACM
- ✅ DNS validation record auto-created
- ✅ HTTPS listener attached with ACM certificate
- ✅ Target group created and attached to ALB
- ✅ ALB provisioned and accessible via `https://yourdomain.com`
- ✅ Private EC2 instances accessible only through ALB (not directly from internet)

---

## Task Completed Summary

| Task | Status |
|---|---|
| Enabled EC2 Hibernation during launch | ✅ Done |
| Ran `uptime` and saved to `/tmp` before hibernation | ✅ Done |
| Hibernated instance and verified `/tmp` persisted after resume | ✅ Done |
| Understood Placement Groups (Cluster, Spread, Partition) | ✅ Done |
| Created Hosted Zone in Route 53 | ✅ Done |
| Requested SSL/TLS certificate from ACM | ✅ Done |
| Created DNS validation record from ACM | ✅ Done |
| Created ALB with HTTPS listener and ACM certificate attached | ✅ Done |
| Created Target Group with private EC2 instances | ✅ Done |
| Verified application accessible via HTTPS custom domain | ✅ Done |

---

*Document generated for AWS learning lab — EC2 Advanced Configuration session*