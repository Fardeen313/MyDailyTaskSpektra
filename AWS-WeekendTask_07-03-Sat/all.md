# Weekly Task Log

---

## Task Info

| Field         | Details                        |
|---------------|-------------------------------|
| **Date**      | Weekend Task                  |
| **Status**    | ✅ Completed                  |
| **Topic**     | Docker on EC2 with CloudWatch & S3 Log Export via EC2 cron job and aws IAM role |

---

## Task Overview

Deploy a Dockerized web application (custom Mario image) on an EC2 instance using a fully automated script and store it in s3 also generate docker application logs and export it into aws cloudwatch and s3 using iam role — provisioned entirely via Terraform — with CloudWatch log monitoring and S3 log archiving via cron.

---

## What Was Done

### 1. Docker Configuration Script (`docker.sh`) → Uploaded to S3

- Script stored in S3 bucket: `s3://dockerconfig12345678/dockerconfig123/docker.sh`
- On execution, it:
  - Updates the system using `dnf`
  - Installs Docker via `dnf install -y docker`
  - Enables, starts, and restarts Docker using `systemctl`
  - Creates a `docker` group and grants socket permissions (`chmod 666 /var/run/docker.sock`)
  - Adds `ec2-user` to the `docker` group via `usermod -aG docker ec2-user`
  - Pulls custom Docker image: `fardeenattar/mario-image:20251104044029`
  - Runs the container on port `8080:80` as `mario-container-01`

> **Custom Image Details:** Built from a personal Dockerfile containing a static web app (`index.html` + `main.js`) served via the container.

---

### 2. EC2 User Data Script (`script.sh`)

Executed automatically on EC2 launch. Steps performed:

1. **Installs CloudWatch Agent** via `dnf install -y amazon-cloudwatch-agent`
2. **Installs AWS CLI** via `dnf install -y awscli`
3. **Copies `docker.sh` from S3** and runs it to set up Docker + pull/run the container
4. **Creates CloudWatch Agent config** at `/opt/aws/amazon-cloudwatch-agent/bin/config.json`:
   - Monitors `/var/lib/docker/containers/*/*.log`
   - Log group: `Dockerapp`
   - Log stream: `{instance_id}-{container_id}`
   - Retention: 1 day
5. **Starts CloudWatch Agent** using `fetch-config` with the above JSON
6. **Installs and enables `cronie`** for cron job support
7. **Creates log upload script** at `/usr/local/bin/dockerlogupload.sh`:
   - Copies Docker container logs to `/var/log/docker-s3/`
   - Uploads each log to S3 with a timestamped filename
   - Cleans up local copies after upload
8. **Registers cron job** to run `dockerlogupload.sh` every minute (`* * * * *`)

---

### 3. Terraform Infrastructure (`main.tf`, `variables.tf`, `terraform.tfvars`)

All infrastructure provisioned via Terraform:

| Resource | Description |
|----------|-------------|
| `aws_s3_bucket` | Creates the config bucket (`dockerconfig12345678`) |
| `aws_s3_object` | Uploads `docker.sh` to S3 at `dockerconfig123/docker.sh` |
| `aws_s3_bucket_policy` | Allows EC2 IAM role (`EC2-CW-S3`) to `PutObject` into the bucket |
| `data.aws_caller_identity` | Fetches current AWS account ID dynamically for IAM ARN |
| `data.aws_iam_instance_profile` | References existing IAM instance profile `EC2-CW-S3` |
| `aws_instance` | Launches EC2 with AMI, key pair, security group, IAM profile, and user data |

**Outputs:**
- `public` → EC2 public IP with port `8080`
- `name` → IAM instance profile ID
- `sg_id` → Security group ID used

**Variables** (`variables.tf` + `terraform.tfvars`):
- `image` — Amazon Linux 2023 AMI ID
- `instance_type` — EC2 instance type
- `key` — Key pair name
- `bucket` — S3 bucket name
- `bucket_key` — Directory path inside bucket
- `security_group_id` — Existing security group ID

---

## Result

| Component | Result |
|-----------|--------|
| Docker setup on EC2 | ✅ Working |
| Custom Docker image pulled & running | ✅ `mario-container-01` on port 8080 |
| CloudWatch Agent streaming container logs | ✅ Log group `Dockerapp` |
| S3 log archiving via cron (every 60s) | ✅ Timestamped logs uploaded |
| Full infra via Terraform | ✅ All resources provisioned |

---

## Architecture Summary

```
Terraform
  ├── S3 Bucket (dockerconfig12345678)
  │     └── docker.sh (setup script)
  └── EC2 Instance (Amazon Linux 2023)
        ├── User Data (script.sh)
        │     ├── Installs CW Agent + AWS CLI
        │     ├── Downloads & runs docker.sh from S3
        │     │     └── Docker → pulls & runs mario-container-01 (:8080)
        │     ├── CloudWatch Agent → streams container logs → Log Group: Dockerapp
        │     └── Cron (* * * * *) → uploads Docker logs → S3 (timestamped)
        └── IAM Role: EC2-CW-S3
```

---
