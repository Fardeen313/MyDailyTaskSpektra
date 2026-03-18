# EC2 Hands-On Tasks Documentation

---

## Task 1: Create an EBS Volume and Attach to a Running EC2 Instance

### Objective
Create an EBS volume in the same Availability Zone as the running EC2 instance, attach it, and mount it to the `/data` directory.

### Steps Performed

1. **Created EBS Volume** in the same AZ as the EC2 instance (`us-east-1c`)
2. **Attached the volume** to the running EC2 instance via AWS Console

   > **Screenshot Reference:** Attached volume `vol-088329ed4ba1b3af0` to instance `i-07eadd359812c8ea3` using device name `/dev/sdf`

   ![Attach Volume Screenshot](./Screenshot_2026-03-10_104507.png)
   ![Device Name Selection](./Screenshot_2026-03-10_104445.png)

   > **Note:** Device name selected was `/dev/sdf`. AWS may rename it internally to `/dev/xvdf` or `/dev/nvme1n1` on newer Linux kernels.

3. **Verified the attachment** using:
   ```bash
   lsblk
   ```
   This shows the newly attached volume (e.g., `nvme1n1`) listed under block devices.

4. **Created the mount directory:**
   ```bash
   mkdir /data
   ```

5. **Mounted the volume:**
   ```bash
   mount /dev/nvme1n1 /data
   ```

6. **Verified the mount:**
   ```bash
   df -h
   ```

### Result
EBS volume successfully created, attached to EC2, and mounted at `/data`.

---

## Task 2: Install Docker via EC2 User Data and Run a Persistent Application

### Objective
Install Docker using EC2 User Data during instance launch and run a containerized application that persists across reboots.

### User Data Script

```bash
#!/bin/bash -xe
dnf yum update -y
sleep 60
dnf update -y
dnf install -y docker
systemctl enable docker
systemctl start docker
systemctl restart docker
systemctl status docker
groupadd docker
chmod 666 /var/run/docker.sock
usermod -aG docker ec2-user
docker pull fardeenattar/mario-image:20251104044029
docker run -d --restart unless-stopped -p 8080:80 --name mario-container-01 fardeenattar/mario-image:20251104044029
```

### Key Points

- `systemctl enable docker` — ensures Docker starts automatically on every reboot
- `--restart unless-stopped` — ensures the container restarts automatically unless manually stopped
- Application runs on port `8080` and is accessible at `http://<EC2-PUBLIC-IP>:8080`

### Result
Docker installed and Mario application container running in persistent mode. Application survives EC2 reboots.

---

## Task 3: Serve Custom Web Page from EBS Volume via Apache, Create AMI, and Launch New Instance

### Objective
Mount an EBS volume, place a custom `index.html` on it, configure Apache HTTPD to serve it, create an AMI from the instance, and launch a new instance from that image.

### Steps Performed

1. **Mounted EBS volume** at `/data` (from Task 1)

2. **Created custom web page:**
   ```bash
   echo "<h1>Hello from EBS Volume!</h1>" > /data/index.html
   ```

3. **Installed Apache HTTPD:**
   ```bash
   yum install -y httpd
   ```

4. **Copied the page to Apache's web root:**
   ```bash
   cp /data/index.html /var/www/html/index.html
   ```

5. **Started and enabled Apache:**
   ```bash
   systemctl start httpd
   systemctl enable httpd
   ```

6. **Restarted Apache after changes:**
   ```bash
   systemctl restart httpd
   ```

7. **Created AMI** from the configured EC2 instance via AWS Console (EC2 → Actions → Image and templates → Create image)

8. **Launched a new EC2 instance** from the created AMI

9. **Accessed the application** via the new instance's Public IP in a browser

### Result
Successfully created AMI from configured EC2, deployed new instance from that image, and accessed the web application via browser using the public IP.

---

## Task 4: EC2 Metrics Dashboard via Apache with Real-Time Graphs

### Objective
Create a real-time metrics dashboard served by Apache that displays EC2 metadata and live system metrics (CPU, Memory, Disk, Network) as dynamic graphs.

### Implementation Overview

The solution uses:
- A **bash script** (`update_metrics.sh`) run via **cron every minute** to collect metrics
- **IMDSv2** for secure EC2 metadata retrieval
- **Bootstrap 5** for UI layout
- **Chart.js** (recommended enhancement) for live graph rendering

### Setup Script Summary

```bash
#!/bin/bash

# Install and start cron
yum install -y cronie
systemctl enable crond
systemctl start crond

# Create the metrics update script at /usr/local/bin/update_metrics.sh
# Script collects:
#   - EC2 Metadata: Instance ID, AMI ID, Instance Type, AZ, Public IP, Private IP, Security Groups
#   - System Metrics: CPU Usage, Memory Usage, Disk Usage, Network I/O

# Run once immediately
/usr/local/bin/update_metrics.sh

# Schedule cron job to run every minute
echo "* * * * * root /usr/local/bin/update_metrics.sh" > /etc/cron.d/metrics_dashboard
chmod 644 /etc/cron.d/metrics_dashboard
```

### Metadata Retrieved (via IMDSv2)

| Field            | Source                                      |
|------------------|---------------------------------------------|
| Instance ID      | `/latest/meta-data/instance-id`             |
| AMI ID           | `/latest/meta-data/ami-id`                  |
| Instance Type    | `/latest/meta-data/instance-type`           |
| Availability Zone| `/latest/meta-data/placement/availability-zone` |
| Public IP        | `/latest/meta-data/public-ipv4`             |
| Private IP       | `/latest/meta-data/local-ipv4`              |
| Security Groups  | `/latest/meta-data/security-groups`         |

### System Metrics Collected

| Metric  | Command Used                                              |
|---------|-----------------------------------------------------------|
| CPU     | `mpstat 1 1` — calculates `100 - idle%`                  |
| Memory  | `free -m` — shows `used/total * 100`                     |
| Disk    | `df -h /` — shows usage percentage of root filesystem    |
| Network | `/proc/net/dev` — cumulative sent/received in MB         |

### Result
Dashboard accessible at `http://<EC2-PUBLIC-IP>/` showing real-time EC2 metadata and system metrics, auto-refreshing every 60 seconds.

> **Enhancement Note:** For truly real-time animated graphs (live CPU/Memory charts that increase and decrease), the dashboard was upgraded to use **Chart.js** with JavaScript polling via `setInterval` — fetching a lightweight JSON metrics endpoint and updating graphs client-side without full page reloads.

---

*Documentation prepared for EC2 hands-on lab tasks covering EBS volumes, Docker, AMI creation, and metrics dashboards.*