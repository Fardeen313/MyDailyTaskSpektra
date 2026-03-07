# AWS Learning Notes – Day 4

Topics Covered

1. Basic Networking Concepts
2. IP Address
3. Gateway
4. Subnet Prefix
5. IP Address Classes
6. CIDR (Classless Inter‑Domain Routing)
7. VPC and CIDR Ranges
8. AWS Reserved IP Addresses
9. Practical VPC Networking Task
10. Bastion Host Access and Server Setup
11. IAM Identity Center Overview

---

# 1. Basic Networking Concepts

## LAN (Local Area Network)

A **LAN** is a network that connects computers within a small geographic area such as:

* Home network
* Office network
* School network

Characteristics:

* High speed
* Private internal communication
* Usually connected through switches and routers

Example:

```
Office Computers
      │
      ▼
    Switch
      │
      ▼
    Router
      │
      ▼
    Internet
```

---

## WAN (Wide Area Network)

A **WAN** connects multiple LAN networks over a large geographic area.

Example:

* The Internet
* Corporate networks connecting multiple branch offices

WAN is typically managed by telecom providers.

---

## Router

A **Router** connects different networks together and forwards data packets between them.

Main functions:

* Connect LAN to Internet
* Route network traffic
* Assign IP addresses using DHCP

Example:

```
LAN Network → Router → Internet
```

---

## Switch

A **Switch** connects multiple devices within the same LAN.

Purpose:

* Enables communication between devices
* Uses MAC addresses to forward data

Example:

```
PC1
PC2  → Switch → Router → Internet
PC3
```

Switch improves network performance by reducing collisions.

---

# 2. What is an IP Address

An **IP Address (Internet Protocol Address)** is a unique identifier assigned to a device on a network.

Purpose:

* Identify devices
* Enable communication between systems

Example IPv4 address:

```
192.168.1.10
```

IPv4 consists of **32 bits** divided into four octets.

Example:

```
192.168.1.10
```

Each section ranges from **0 – 255**.

---

# 3. What is a Gateway

A **Gateway** is a device that connects one network to another network.

In most networks, the gateway is the **router IP address**.

Example:

```
Computer → Gateway → Internet
```

In AWS VPC:

* Internet Gateway connects VPC to Internet
* NAT Gateway allows private subnet internet access

---

# 4. Subnet Prefix

A **Subnet Prefix** defines how many bits of the IP address belong to the network portion.

Example:

```
192.168.1.0/24
```

Here:

* 24 bits = network portion
* Remaining bits = host portion

This determines how many hosts can exist in the subnet.

---

# 5. IP Address Classes

IPv4 addresses are divided into different classes.

| Class | Range                       | Purpose         |
| ----- | --------------------------- | --------------- |
| A     | 1.0.0.0 – 126.0.0.0         | Large networks  |
| B     | 128.0.0.0 – 191.255.0.0     | Medium networks |
| C     | 192.0.0.0 – 223.255.255.0   | Small networks  |
| D     | 224.0.0.0 – 239.255.255.255 | Multicast       |
| E     | 240.0.0.0 – 255.255.255.255 | Reserved        |

Class C is commonly used for small networks.

---

# 6. CIDR (Classless Inter-Domain Routing)

CIDR is a modern method of allocating IP addresses.

Format:

```
IP Address / Prefix Length
```

Example:

```
10.0.0.0/16
```

Formula for number of IP addresses:

```
2^n
```

Where:

```
n = number of host bits
```

Example:

```
/24 subnet
Host bits = 8
Total IPs = 2^8 = 256
```

---

# 7. VPC Explanation

A **VPC (Virtual Private Cloud)** is a logically isolated network in AWS where you launch resources.

You control:

* IP ranges
* Subnets
* Route tables
* Internet connectivity

Example CIDR range for VPC:

```
10.0.0.0/16
```

Network bits = 16
Host bits = 16

---

# 8. AWS Reserved IP Addresses

In each AWS subnet, **5 IP addresses are reserved** and cannot be used.

Example subnet:

```
10.0.1.0/24
```

Reserved addresses:

| IP   | Purpose         |
| ---- | --------------- |
| .0   | Network address |
| .1   | Default router  |
| .2   | DNS server      |
| .3   | Future AWS use  |
| .255 | Broadcast       |

Usable IPs = Total IPs – 5

---

# 9. Practical VPC Networking Task

Infrastructure created:

```
VPC
 ├── Public Subnet
 │       └── Public EC2 Instance
 │
 └── Private Subnet
         └── Private EC2 Instance
```

Components created:

* VPC
* 2 Subnets
* 2 Route Tables
* Internet Gateway
* NAT Gateway

---

## Route Table Setup

### Public Route Table

Associated with **Public Subnet**.

Route:

```
0.0.0.0/0 → Internet Gateway
```

This allows internet access.

---

### Private Route Table

Associated with **Private Subnet**.

Route:

```
0.0.0.0/0 → NAT Gateway
```

Private instances can access the internet but **cannot receive inbound traffic**.

---

# 10. Bastion Host Access

Instances created:

* EC2 with **Public IP** in Public Subnet
* EC2 without **Public IP** in Private Subnet

Connection flow:

```
Local Machine
     │
     ▼
Public EC2 (Bastion Host)
     │
     ▼
Private EC2 Server
```

Steps performed:

1. SSH into Bastion Host
2. Copy private server `.pem` file
3. Change permissions

```
chmod 400 key.pem
```

4. SSH into private instance

```
ssh -i key.pem ec2-user@private-ip
```

---

## Software Installed on Private Server

Installed packages:

```
nginx
httpd
git
python3
```

These were installed after accessing the private server through the bastion host.
![Network Setup](<Screenshot 2026-03-05 134726.png>)
![Private EC2](<Screenshot 2026-03-05 134532.png>)
![Bastion Host and Private Server Running](<Screenshot 2026-03-05 134451.png>)
![Bastion](<Screenshot 2026-03-05 133307.png>)
![Installed Git, Python3, HTTPD, nginx](<Screenshot 2026-03-05 134406.png>)

---


# 11. IAM Identity Center Overview

**IAM Identity Center** (previously AWS SSO) allows centralized identity and access management for multiple AWS accounts.

It helps organizations:

* Manage user access centrally
* Provide single sign-on to AWS accounts
* Integrate with corporate identity providers

Main features:

* Centralized user management
* Single Sign-On (SSO)
* Multi-account access
* Integration with Active Directory

Architecture example:

```
Users
   │
   ▼
IAM Identity Center
   │
   ▼
AWS Organizations Accounts
```

Benefits:

* Simplifies login process
* Improves security
* Reduces IAM user management in individual accounts

---

# End of Day 4 Notes
