# AWS Learning Notes – Day 3

Topics Covered

1. VPC Overview
2. CIDR, Network Bits, Host Bits
3. Reserved IP Addresses
4. Reliability and High Availability Concepts
5. VPC Practical Task – Multi‑Subnet Architecture
6. Bastion Host Access to Private Instance
7. IAM Best Practices
8. IAM Hands‑On Tasks

---

# 1. VPC Overview

Amazon **VPC (Virtual Private Cloud)** allows you to create an isolated virtual network inside AWS where you can launch AWS resources.

Inside a VPC you control:

* IP address ranges
* Subnets
* Route tables
* Internet connectivity
* Security rules

A VPC acts similar to a **private datacenter network in the cloud**.

Basic VPC Architecture

```
AWS Region
   │
   └── VPC
        ├── Subnets
        ├── Route Tables
        ├── Internet Gateway
        ├── NAT Gateway
        ├── Security Groups
        └── Network ACLs
```

---

# 2. CIDR, Network Bits and Host Bits

VPC IP addressing uses **CIDR (Classless Inter‑Domain Routing)**.

Example CIDR block:

```
10.0.0.0/16
```

Explanation:

* `/16` = Network bits
* Remaining bits = Host bits

Formula for number of IP addresses:

```
2^n
```

Where:

```
n = number of host bits
```

Example

```
10.0.0.0/24
Host bits = 8
Total IPs = 2^8 = 256
```

---

# 3. Reserved IP Addresses in AWS

In every subnet AWS reserves **5 IP addresses** for internal purposes.

Example subnet:

```
10.0.1.0/24
```

Reserved IPs:

| IP   | Purpose         |
| ---- | --------------- |
| .0   | Network address |
| .1   | VPC router      |
| .2   | DNS             |
| .3   | Future AWS use  |
| .255 | Broadcast       |

Usable IPs = Total IPs − 5

---

# 4. Reliability and High Availability

**Reliability** means the system continues working correctly without failure.

**High Availability (HA)** means the application remains accessible even if some components fail.

AWS provides reliability and high availability using multiple architectural practices.

### Key Reliability and High Availability Techniques

1. **Multi‑Availability Zone Deployment**
   Deploy resources in multiple AZs so if one AZ fails the application continues running.

2. **Load Balancers (ALB / NLB)**
   Distribute incoming traffic across multiple instances to avoid single point of failure.

3. **Auto Scaling**
   Automatically launch or terminate EC2 instances based on demand and health checks.

4. **Redundant Subnets**
   Create subnets across different AZs for fault tolerance.

5. **Health Checks and Monitoring**
   Use CloudWatch and Load Balancer health checks to detect unhealthy instances.

6. **Elastic IPs and Failover**
   Allow quick remapping of public IPs to replacement instances.

7. **NAT Gateways in Multiple AZs**
   Improves reliability for private subnet internet access.

8. **Decoupled Architecture**
   Use services like SQS, SNS, and Lambda to reduce tight dependency between components.

### Example High Availability Network Design

```
Region
   │
   ├── AZ-1
   │     ├── Public Subnet
   │     └── Private Subnet
   │
   └── AZ-2
         ├── Public Subnet
         └── Private Subnet
```

If AZ‑1 fails, workloads in **AZ‑2 continue serving traffic**, ensuring application availability.

---

# 5. VPC Practical Task – Network Architecture

Objective:

Create a VPC architecture with public and private subnets.

Architecture created:

```
VPC
 ├── Public Route Table
 │       ├── Public Subnet 1
 │       └── Public Subnet 2
 │
 └── Private Route Table
         ├── Private Subnet 1
         └── Private Subnet 2
```

Components created:

* 1 VPC
* 4 Subnets
* 2 Route Tables
* Internet Gateway
* NAT Gateway

---

## Route Table Configuration

### Public Route Table

Associated with:

* Public Subnet 1
* Public Subnet 2

Route rule:

```
Destination : 0.0.0.0/0
Target : Internet Gateway
```

---

### Private Route Table

Associated with:

* Private Subnet 1
* Private Subnet 2

Route rule:

```
Destination : 0.0.0.0/0
Target : NAT Gateway
```

This allows private instances to access internet **without exposing them publicly**.

---

# 6. Bastion Host Access to Private Instance

Instances created:

* Bastion Host in Public Subnet
* Private EC2 Instance in Private Subnet

Access flow:

```
Local Machine
     │
     ▼
Bastion Host (Public Subnet)
     │
     ▼
Private EC2 Instance (Private Subnet)
```

Steps performed:

1. Connect to Bastion Host using SSH
2. Copy private instance `.pem` file
3. SSH from bastion host into private instance

Example command

```
ssh -i private-key.pem ec2-user@private-ip
```

---

# 7. IAM Best Practices

Important IAM security practices:

* Enable **MFA for all users**
* Follow **least privilege principle**
* Do not share **Access Keys or Secret Keys**
* Rotate access keys regularly
* Use **IAM Groups instead of direct user permissions**
* Use **IAM Roles for services** instead of access keys
* Enable **CloudTrail logging**
* Use **permission boundaries for delegated admins**
* Monitor IAM activity with CloudWatch
* Disable or delete unused credentials

---

# 8. IAM Hands‑On Tasks

## Task 1 – Restrict AWS Usage to Two Regions

Objective:

Allow all AWS services but **only in specific regions**.

Allowed Regions:

* us-east-1
* us-east-2

Policy:

```
{
 "Version": "2012-10-17",
 "Statement": [
  {
   "Sid": "Statement1",
   "Effect": "Allow",
   "Action": "*",
   "Resource": "*",
   "Condition": {
    "StringEquals": {
     "aws:RequestedRegion": [
      "us-east-1",
      "us-east-2"
     ]
    }
   }
  }
 ]
}
```

---

## Task 2 – Restrict EC2 Instance Configuration

Objective:

Allow EC2 instance creation only when:

* Region = us-east-1
* Instance types allowed
* Volume type = gp2
* Volume size = up to 30GB

Policy Result:

```
{
 "Version": "2012-10-17",
 "Statement": [
  {
   "Sid": "AllowAllInUSEast1",
   "Effect": "Allow",
   "Action": "*",
   "Resource": "*",
   "Condition": {
    "StringEquals": {
     "aws:RequestedRegion": "us-east-1"
    }
   }
  },
  {
   "Sid": "DenyOutsideUSEast1",
   "Effect": "Deny",
   "Action": "*",
   "Resource": "*",
   "Condition": {
    "StringNotEquals": {
     "aws:RequestedRegion": "us-east-1"
    }
   }
  },
  {
   "Sid": "RestrictEC2InstanceTypes",
   "Effect": "Deny",
   "Action": "ec2:RunInstances",
   "Resource": "*",
   "Condition": {
    "StringNotEquals": {
     "ec2:InstanceType": [
      "t2.micro",
      "t2.nano",
      "t3.micro",
      "t3.small"
     ]
    }
   }
  },
  {
   "Sid": "RestrictVolumeType",
   "Effect": "Deny",
   "Action": [
    "ec2:RunInstances",
    "ec2:CreateVolume"
   ],
   "Resource": "*",
   "Condition": {
    "StringNotEquals": {
     "ec2:VolumeType": "gp2"
    }
   }
  },
  {
   "Sid": "RestrictVolumeSize",
   "Effect": "Deny",
   "Action": [
    "ec2:RunInstances",
    "ec2:CreateVolume"
   ],
   "Resource": "*",
   "Condition": {
    "NumericNotEquals": {
     "ec2:VolumeSize": 30
    }
   }
  }
 ]
}
```

---

## Task 3 – EC2 IAM Role for S3 and Lambda Access

Objective:

Create IAM roles that allow EC2 to access **S3 and Lambda services**.

Two implementations created:

1. Using **AWS Managed Policies**
2. Using **Customer Managed Policies**

Role Name:

```
ec2-s3-lambda-full-role
```

Customer Managed Policy – Lambda

```
{
 "Version": "2012-10-17",
 "Statement": [
  {
   "Effect": "Allow",
   "Action": "lambda:*",
   "Resource": "*"
  }
 ]
}
```

Customer Managed Policy – S3

```
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

Result:

EC2 instances using this role can access **all S3 and Lambda operations** without storing credentials on the instance.

---

# End of Day 3 Notes & Tasks
