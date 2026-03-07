# AWS Training – Day 5

## 1. Assessments on Previously Covered Topics

On Day 5, assessments were completed based on the concepts learned in previous training sessions.
These assessments helped reinforce both **theoretical knowledge and practical AWS skills**.

### Topics Covered in the Assessment

* AWS Organizations
* IAM (Users, Roles, Policies)
* CloudWatch
* VPC and Networking
* Subnets and Route Tables
* Internet Gateway and NAT Gateway
* Bastion Host Architecture
* Basic EC2 and Linux commands

The purpose of the assessment was to validate understanding of **AWS architecture, networking, and security concepts**.

---

# 2. EC2 User Data Automation Task

## Objective

To automate EC2 instance configuration using **User Data scripts** during instance launch.

### Task Goals

Automatically configure an **Amazon Linux 2023 EC2 instance** to:

1. Update system packages
2. Install and start **Apache HTTP Server (httpd)**
3. Deploy a **custom HTML webpage**
4. Install **AWS CLI**
5. Create sample files
6. Create an **S3 bucket**
7. Upload files to the S3 bucket

---

# 3. What is EC2 User Data?

**User Data** is a script that automatically runs when an **EC2 instance launches for the first time**.

### Why User Data is Used

* Automates server configuration
* Eliminates manual setup
* Useful for **DevOps automation**
* Helps initialize infrastructure
* Commonly used with **Auto Scaling groups**

---

# 4. User Data Script Used

```bash
#!/bin/bash

sudo dnf update -y
sudo dnf install httpd -y
sudo systemctl start httpd
sudo systemctl enable httpd

sudo bash -c 'cat > /var/www/html/index.html <<EOF
<html>
<head>
<title>Welcome</title>
<style>
body {
  background-color: #0f172a;
  font-family: Arial;
  text-align: center;
  color: white;
}
h1 {
  color: #22c55e;
}
p {
  color: #38bdf8;
  font-size: 20px;
}
.box {
  margin-top: 100px;
  padding: 30px;
  border: 2px solid #22c55e;
  display: inline-block;
  border-radius: 10px;
}
</style>
</head>
<body>
<div class="box">
<h1>Amazon Linux 2023 Web Server</h1>
<p>HTTPD Installed Successfully</p>
<p>Server Powered by EC2</p>
</div>
</body>
</html>
EOF'

sudo dnf install unzip -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

mkdir samplefiles
echo "Sample File 1" > samplefiles/file1.txt
echo "Sample File 2" > samplefiles/file2.txt
echo "Sample File 3" > samplefiles/file3.txt

sudo aws s3 mb s3://fardeen3138888313545
sudo aws s3 cp samplefiles s3://fardeen3138888313545 --recursive
```

---

# 5. Script Execution Explanation

## System Update

```bash
sudo dnf update -y
```

Updates all system packages to the latest version.

---

## Install Apache Web Server

```bash
sudo dnf install httpd -y
```

Installs **Apache HTTP Server** on the EC2 instance.

---

## Start and Enable Apache

```bash
sudo systemctl start httpd
sudo systemctl enable httpd
```

* Starts the web server
* Ensures the server runs automatically after reboot

---

## Deploy Custom HTML Page

A custom webpage is created inside:

```
/var/www/html/index.html
```

The page becomes accessible using the **EC2 Public IP**.

Example:

```
http://<EC2-Public-IP>
```

---

## Install AWS CLI

The script installs **AWS CLI v2** by:

1. Downloading the installation package
2. Extracting the archive
3. Installing AWS CLI

This allows the EC2 instance to interact with AWS services such as **Amazon S3**.

---

## Create Sample Files

A directory named **samplefiles** is created.

Example files:

```
file1.txt
file2.txt
file3.txt
```

Each file contains sample text.

---

## Create S3 Bucket

```
aws s3 mb s3://fardeen3138888313545
```

Creates a new **Amazon S3 bucket**.

Note:
S3 bucket names must be **globally unique across AWS**.

---

## Upload Files to S3

```
aws s3 cp samplefiles s3://fardeen3138888313545 --recursive
```

Uploads all files from the **samplefiles directory** to the S3 bucket.

---

# 6. IAM Role Attached to EC2

An IAM role named:

```
ec2-s3
```

was attached to the EC2 instance.

This role provides **Full Access to Amazon S3**.

### Attached Policy

```
AmazonS3FullAccess
```

### Example Policy JSON

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
```

This permission allows the EC2 instance to:

* Create S3 buckets
* Upload files
* Download files
* List buckets
* Manage objects in S3

---

# 7. Architecture Flow

```
EC2 Instance Launch
        │
        ▼
User Data Script Executes
        │
        ▼
Install HTTPD Web Server
        │
        ▼
Deploy Custom HTML Page
        │
        ▼
Install AWS CLI
        │
        ▼
Create Sample Files
        │
        ▼
Create S3 Bucket
        │
        ▼
Upload Files to S3
```

---

# 8. Key Learning Outcomes

From this task we learned:

* EC2 **User Data automation**
* Installing and configuring **web servers automatically**
* Deploying **custom HTML pages**
* Installing and using **AWS CLI**
* Creating **S3 buckets using CLI**
* Uploading files to S3
* Attaching **IAM roles to EC2**

This demonstrates how **server configuration and cloud resource management can be automated**, which is a fundamental concept in **DevOps and Cloud Engineering**.

---

