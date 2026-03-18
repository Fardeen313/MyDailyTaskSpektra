# AWS CloudFormation Lab — March 18, 2026

---

## ✅ Today's Tasks

### 1. S3 Bucket with IAM Instance Profile on EC2
- Created S3 bucket `onetwothree456987`
- Created IAM Role for EC2 with `s3:ListBucket` scoped **only** to `arn:aws:s3:::onetwothree456987`
- Attached IAM Role via Instance Profile to EC2
- Key learnings:
  - `s3:ListAllMyBuckets` requires `Resource: "*"` (AWS-enforced, service-level action)
  - `s3:ListBucket` can be scoped to a specific bucket ARN
  - CloudFormation has **no native `AWS::S3::Object`** resource — Lambda Custom Resource or UserData script required to create objects

---

### 2. EC2 + S3 CFT (Stack 1 — `MyVPC`)
- VPC: `10.0.0.0/16`
- EC2: `t3.micro`, Amazon Linux 2023, public subnet
- S3 bucket with `s3:ListBucket` permission scoped to specific bucket only
- IAM Role + Instance Profile attached to EC2
- Nginx installed via UserData
- Password authentication enabled for `ec2-user`

**CFT Resources:**
| Resource | Details |
|---|---|
| `MyVPC` | CIDR `10.0.0.0/16` |
| `MyS3Bucket` | `hjgshjsjhfjhdhvhkh` |
| `EC2S3Role` | `s3:ListBucket` on specific bucket only |
| `EC2InstanceProfile` | Wraps EC2S3Role |
| `MyEC2Instance` | `t3.micro`, public subnet, Nginx |
| `MySecurityGroup` | SSH (22), HTTP (80) |

**Connect command from EC2:**
```bash
aws s3 ls s3://hjgshjsjhfjhdhvhkh
```

---

### 3. EC2 + RDS MySQL CFT (Stack 2 — `ProdVPC`)
- VPC: `192.168.0.0/16` (different from Stack 1)
- EC2 public, RDS MySQL private — no IAM, no S3
- MySQL client installed via UserData using `dnf install -y mariadb105` (AL2023 correct package)
- RDS port 3306 open **only** from EC2 Security Group

**CFT Resources:**
| Resource | Details |
|---|---|
| `ProdVPC` | CIDR `192.168.0.0/16` |
| `PublicSubnet1/2` | `192.168.1-2.0/24` |
| `PrivateSubnet1/2` | `192.168.3-4.0/24` (RDS) |
| `EC2SecurityGroup` | SSH (22), HTTP (80) |
| `RDSSecurityGroup` | Port 3306 from EC2SG only |
| `MyRDSInstance` | MySQL 8.0, `db.t3.micro`, private |
| `MyEC2Instance` | `t3.micro`, public, mariadb105 client |

**Connect to RDS from EC2:**
```bash
mysql -h <RDSEndpoint> -u admin -p
```

---

### 4. Key Fixes & Learnings Today

| Issue | Fix |
|---|---|
| `yum install mysql` fails on AL2023 | Use `dnf install -y mariadb105` |
| S3 bucket creation failed (rollback) | Bucket name already taken globally — rename it |
| `aws s3 ls` gave AccessDenied | Expected — `s3:ListAllMyBuckets` not granted by design |
| CloudFormation has no `AWS::S3::Object` | Use Lambda Custom Resource or UserData script |
| `s3:ListAllMyBuckets` needs `Resource: "*"` | AWS-enforced — cannot scope to a bucket ARN |

---

## 📝 Homework (Given Yesterday)

### Task 1 — CFT: EC2 + S3 + IAM
- [ ] Create a CloudFormation template with:
  - VPC + public subnet + IGW
  - EC2 instance with Nginx
  - S3 bucket
  - IAM Role with `s3:ListBucket` scoped to **only that bucket**
  - IAM Instance Profile attached to EC2
- [ ] Verify: `aws s3 ls s3://<bucket>` works from EC2
- [ ] Verify: `aws s3 ls` (list all) is denied

### Task 2 — CFT: EC2 + RDS MySQL (Private)
- [ ] Create a CloudFormation template with:
  - VPC with public + private subnets (2 AZs each)
  - EC2 in public subnet
  - RDS MySQL in private subnet (`PubliclyAccessible: false`)
  - RDS Security Group allowing port 3306 **only** from EC2 Security Group
  - MySQL client (`mariadb105`) installed on EC2 via UserData
- [ ] Deploy and connect: `mysql -h <RDSEndpoint> -u admin -p`

### Task 3 — Concepts to Review
- [ ] Difference between `s3:ListBucket` vs `s3:ListAllMyBuckets`
- [ ] Why RDS needs a **DB Subnet Group** with minimum 2 AZs
- [ ] Why `yum` is replaced by `dnf` on Amazon Linux 2023
- [ ] How CloudFormation Custom Resources work (Lambda-backed)
- [ ] IAM Instance Profile vs IAM Role — what's the difference

---

*Date: March 18, 2026 | Region: ap-south-1*