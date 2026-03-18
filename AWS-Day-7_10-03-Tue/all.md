# EC2 Hands-On Tasks Documentation

---

## Task 1: Create an EBS Volume and Attach to a Running EC2 Instance

### Objective
Create an EBS volume in the same Availability Zone as the running EC2 instance, attach it, and mount it to the `/data` directory.

### Steps Performed

1. **Created EBS Volume** in the same AZ as the EC2 instance (`us-east-1c`)
2. **Attached the volume** to the running EC2 instance via AWS Console

   > **Screenshot Reference:** Attached volume `vol-088329ed4ba1b3af0` to instance `i-07eadd359812c8ea3` using device name `/dev/sdf`

   ![alt text](<Screenshot 2026-03-10 104445.png>)
   ![alt text](<Screenshot 2026-03-10 104507.png>)

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
Create a real-time metrics dashboard served by Apache that displays EC2 metadata and live system metrics (CPU, Memory, Disk, Network) as dynamic animated graphs.

### Implementation Overview

The solution uses two files:

| File | Location | Purpose |
|------|----------|---------|
| `setup_dashboard.sh` | Run once as root | Installs deps, creates both scripts below, seeds cron |
| `update_metrics.sh` | `/usr/local/bin/` | Runs every 60 s via cron — writes `metrics.json` |
| `index.html` | `/var/www/html/` | Static dashboard — polls `metrics.json` every 5 s via JS |

**Key design:** The HTML page is written **once** and never regenerated. The browser fetches `metrics.json` every 5 seconds using `setInterval` + `fetch()`, and Chart.js updates the live line graphs client-side — no page reload needed.

---

### Source Code

#### File 1 — `setup_dashboard.sh` (run once to bootstrap everything)

```bash
#!/bin/bash

# ─────────────────────────────────────────────
# 1. Install dependencies
# ─────────────────────────────────────────────
if ! rpm -q cronie &>/dev/null; then
    echo "Installing cronie..."
    yum install -y cronie
fi

# Install sysstat for mpstat
if ! rpm -q sysstat &>/dev/null; then
    echo "Installing sysstat..."
    yum install -y sysstat
fi

systemctl enable crond
systemctl start crond
echo "Cron service started."

# ─────────────────────────────────────────────
# 2. Create the metrics JSON endpoint script
#    Outputs /var/www/html/metrics.json every minute
# ─────────────────────────────────────────────
cat << 'METRICS_EOF' > /usr/local/bin/update_metrics.sh
#!/bin/bash

WEB_DIR=/var/www/html

# ── EC2 Metadata (IMDSv2) ──────────────────────────────────────────────────
TOKEN=$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

METADATA_BASE="http://169.254.169.254/latest/meta-data"

fetch_meta() {
    curl -sf -H "X-aws-ec2-metadata-token: ${TOKEN}" "${METADATA_BASE}/$1"
}

INSTANCE_ID=$(fetch_meta instance-id)
AMI_ID=$(fetch_meta ami-id)
INSTANCE_TYPE=$(fetch_meta instance-type)
AVAILABILITY_ZONE=$(fetch_meta placement/availability-zone)
PUBLIC_IP=$(fetch_meta public-ipv4)
PRIVATE_IP=$(fetch_meta local-ipv4)
SECURITY_GROUPS=$(fetch_meta security-groups | tr '\n' ',' | sed 's/,$//')

# ── System Metrics ─────────────────────────────────────────────────────────
CPU=$(mpstat 1 1 | awk '/Average/ {printf "%.1f", 100 - $12}')
MEMORY=$(free -m | awk '/Mem:/ {printf "%.1f", $3/$2*100}')
DISK=$(df / | awk 'NR==2 {printf "%.1f", $3/$2*100}')

# Network bytes (pick first matching interface)
NET_LINE=$(grep -E '^\s*(eth0|ens|enp)' /proc/net/dev | head -1)
TX_MB=$(echo "$NET_LINE" | awk '{printf "%.2f", $10/1024/1024}')
RX_MB=$(echo "$NET_LINE" | awk '{printf "%.2f", $2/1024/1024}')

TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')

# ── Write JSON metrics file (polled by the browser every 5 s) ─────────────
cat > "${WEB_DIR}/metrics.json" << JSON
{
  "timestamp": "${TIMESTAMP}",
  "metadata": {
    "instance_id":       "${INSTANCE_ID}",
    "ami_id":            "${AMI_ID}",
    "instance_type":     "${INSTANCE_TYPE}",
    "availability_zone": "${AVAILABILITY_ZONE}",
    "public_ip":         "${PUBLIC_IP}",
    "private_ip":        "${PRIVATE_IP}",
    "security_groups":   "${SECURITY_GROUPS}"
  },
  "metrics": {
    "cpu":    ${CPU:-0},
    "memory": ${MEMORY:-0},
    "disk":   ${DISK:-0},
    "net_tx": ${TX_MB:-0},
    "net_rx": ${RX_MB:-0}
  }
}
JSON

METRICS_EOF

chmod +x /usr/local/bin/update_metrics.sh

# ─────────────────────────────────────────────
# 3. Write the static HTML dashboard
#    (polls metrics.json every 5 s via fetch)
# ─────────────────────────────────────────────
cat << 'HTML_EOF' > /var/www/html/index.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EC2 Metrics Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    body { background: #0f1117; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
    h1   { color: #38bdf8; font-weight: 700; }
    h4   { color: #94a3b8; text-transform: uppercase; letter-spacing: .08em; font-size: .75rem; }
    .card {
      background: #1e2130;
      border: 1px solid #2d3148;
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
      margin-bottom: 1rem;
    }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #38bdf8; }
    .meta-value   { font-size: .9rem; color: #cbd5e1; word-break: break-all; }
    .chart-wrap   { position: relative; height: 180px; }
    #lastUpdate   { font-size: .8rem; color: #64748b; }
  </style>
</head>
<body class="p-3">
<div class="container-fluid">

  <div class="d-flex align-items-center justify-content-between mb-3">
    <h1 class="mb-0">⚡ EC2 Metrics Dashboard</h1>
    <span id="lastUpdate">Waiting for data…</span>
  </div>

  <!-- ── Metadata cards ───────────────────────────────────────────── -->
  <div class="row g-2 mb-4" id="metaRow">
    <div class="col-md-3 col-6"><div class="card"><h4>Instance ID</h4>     <div class="meta-value" id="m-instance_id">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card"><h4>AMI ID</h4>          <div class="meta-value" id="m-ami_id">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card"><h4>Instance Type</h4>   <div class="meta-value" id="m-instance_type">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card"><h4>AZ</h4>              <div class="meta-value" id="m-availability_zone">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card"><h4>Public IP</h4>       <div class="meta-value" id="m-public_ip">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card"><h4>Private IP</h4>      <div class="meta-value" id="m-private_ip">—</div></div></div>
    <div class="col-md-6">     <div class="card"><h4>Security Groups</h4>  <div class="meta-value" id="m-security_groups">—</div></div></div>
  </div>

  <!-- ── Live numeric tiles ───────────────────────────────────────── -->
  <div class="row g-2 mb-4">
    <div class="col-md-3 col-6"><div class="card text-center"><h4>CPU</h4>      <div class="metric-value" id="v-cpu">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card text-center"><h4>Memory</h4>   <div class="metric-value" id="v-mem">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card text-center"><h4>Disk</h4>     <div class="metric-value" id="v-disk">—</div></div></div>
    <div class="col-md-3 col-6"><div class="card text-center"><h4>Net TX/RX</h4><div class="metric-value" id="v-net" style="font-size:1rem">—</div></div></div>
  </div>

  <!-- ── Real-time line charts ────────────────────────────────────── -->
  <div class="row g-2">
    <div class="col-md-4"><div class="card"><h4>CPU Usage (%)</h4>    <div class="chart-wrap"><canvas id="cpuChart"></canvas></div></div></div>
    <div class="col-md-4"><div class="card"><h4>Memory Usage (%)</h4> <div class="chart-wrap"><canvas id="memChart"></canvas></div></div></div>
    <div class="col-md-4"><div class="card"><h4>Disk Usage (%)</h4>   <div class="chart-wrap"><canvas id="diskChart"></canvas></div></div></div>
  </div>

</div>

<script>
// ── Chart factory ───────────────────────────────────────────────────────
const MAX_POINTS = 20;

function makeChart(id, label, color) {
  const ctx = document.getElementById(id).getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label,
        data: [],
        borderColor: color,
        backgroundColor: color + '22',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: color,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      animation: { duration: 400 },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: '#64748b', maxTicksLimit: 5 }, grid: { color: '#2d3148' } },
        y: { min: 0, max: 100,
             ticks: { color: '#64748b', callback: v => v + '%' },
             grid: { color: '#2d3148' } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

const cpuChart  = makeChart('cpuChart',  'CPU %',  '#38bdf8');
const memChart  = makeChart('memChart',  'Mem %',  '#a78bfa');
const diskChart = makeChart('diskChart', 'Disk %', '#34d399');

// ── Slide-in new data point, drop oldest ───────────────────────────────
function push(chart, label, value) {
  if (chart.data.labels.length >= MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  chart.update();
}

// ── Poll /metrics.json every 5 s ───────────────────────────────────────
async function poll() {
  try {
    const res = await fetch('/metrics.json?t=' + Date.now());
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const d = await res.json();

    const ts    = new Date(d.timestamp);
    const label = ts.toLocaleTimeString();

    // Update metadata cards
    for (const [k, v] of Object.entries(d.metadata)) {
      const el = document.getElementById('m-' + k);
      if (el) el.textContent = v || '—';
    }

    // Update numeric tiles
    const m = d.metrics;
    document.getElementById('v-cpu').textContent  = m.cpu.toFixed(1)    + '%';
    document.getElementById('v-mem').textContent  = m.memory.toFixed(1) + '%';
    document.getElementById('v-disk').textContent = m.disk.toFixed(1)   + '%';
    document.getElementById('v-net').textContent  =
      '↑ ' + m.net_tx.toFixed(2) + ' MB  ↓ ' + m.net_rx.toFixed(2) + ' MB';

    // Push to charts
    push(cpuChart,  label, m.cpu);
    push(memChart,  label, m.memory);
    push(diskChart, label, m.disk);

    document.getElementById('lastUpdate').textContent = 'Updated: ' + ts.toLocaleTimeString();
  } catch (e) {
    document.getElementById('lastUpdate').textContent = 'Error: ' + e.message;
  }
}

poll();                        // run immediately on page load
setInterval(poll, 5000);      // then every 5 seconds
</script>
</body>
</html>
HTML_EOF

echo "Dashboard HTML written to /var/www/html/index.html"

# ─────────────────────────────────────────────
# 4. Seed metrics.json immediately
# ─────────────────────────────────────────────
/usr/local/bin/update_metrics.sh
echo "Initial metrics.json created."

# ─────────────────────────────────────────────
# 5. Install cron job — runs every minute
# ─────────────────────────────────────────────
echo "* * * * * root /usr/local/bin/update_metrics.sh" > /etc/cron.d/metrics_dashboard
chmod 644 /etc/cron.d/metrics_dashboard
echo "Cron job installed (every 60 s)."

echo ""
echo "✅ Setup complete. Open http://<EC2-PUBLIC-IP>/ to view the dashboard."
```

---

### Metadata Retrieved (via IMDSv2)

| Field             | IMDSv2 Path                                          |
|-------------------|------------------------------------------------------|
| Instance ID       | `/latest/meta-data/instance-id`                      |
| AMI ID            | `/latest/meta-data/ami-id`                           |
| Instance Type     | `/latest/meta-data/instance-type`                    |
| Availability Zone | `/latest/meta-data/placement/availability-zone`      |
| Public IP         | `/latest/meta-data/public-ipv4`                      |
| Private IP        | `/latest/meta-data/local-ipv4`                       |
| Security Groups   | `/latest/meta-data/security-groups`                  |

### System Metrics Collected

| Metric  | Command         | Notes                                                        |
|---------|-----------------|--------------------------------------------------------------|
| CPU     | `mpstat 1 1`    | `100 - idle%` → active CPU usage                             |
| Memory  | `free -m`       | `used / total * 100`                                         |
| Disk    | `df /`          | `used / total * 100` (no `-h` — returns raw numbers for math)|
| Network | `/proc/net/dev` | Cumulative TX / RX in MB                                     |

### Syntax Fixes Applied (vs Original Script)

| Original Issue | Fix Applied |
|---|---|
| `sysstat` not installed → `mpstat` silently failed | Added `rpm -q sysstat` check + auto-install |
| `$NET` embedded `<br>` HTML into bash heredoc | Replaced with structured JSON fields `net_tx` / `net_rx` |
| Inner heredoc `<<HTML` inside outer `<<'EOF'` caused premature variable expansion | Separated into two independent scripts |
| `grep -E 'eth0\|ens'` matched partial names | Anchored with `^\s*` + added `enp` + `head -1` guard |
| `df -h` returned human string `"45%"` — unusable as a number in JSON | Changed to plain `df /` and computed float with `awk` |

### Result

Dashboard accessible at `http://<EC2-PUBLIC-IP>/` with:
- **EC2 metadata** cards populated from IMDSv2
- **CPU, Memory, Disk** shown as live animated line graphs (last 20 data points)
- **Network TX/RX** shown as cumulative MB counter
- Browser polls `metrics.json` every **5 seconds** — graphs animate in real time without any page reload