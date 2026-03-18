# AWS CloudFormation Lab — March 18, 2026

> **Region:** `ap-south-1` | **AMI:** Amazon Linux 2023

---

## ✅ Today's Tasks

---

### Task 1 — Deploy VPC + EC2 + S3 Bucket + IAM Instance Profile via CloudFormation

**Objective:** Provision a complete networking stack with an EC2 instance that has scoped IAM access to a specific S3 bucket, with Nginx running and password authentication enabled — all through a single CloudFormation template.

#### CFT: `stack1-vpc-ec2-s3-iam.yaml`

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: VPC with IGW, subnets, route table, SG, EC2 with Nginx, S3 bucket, and IAM instance profile

# ========================
# PARAMETERS
# ========================
Parameters:
  LatestAmazonLinuxAMI:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64
  Password:
    Type: String
    NoEcho: true
    Description: Password for ec2-user
    MinLength: 8

# ========================
# RESOURCES
# ========================
Resources:

  # ── S3 Bucket ──────────────────────────────────────────────
  MyS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: hjgshjsjhfjhdhvhkh

  # ── IAM Role for EC2 ───────────────────────────────────────
  EC2S3Role:
    Type: AWS::IAM::Role
    Properties:
      RoleName: EC2S3ListRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: ec2.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: S3ListPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Sid: ListBucketContents
                Effect: Allow
                Action:
                  - s3:ListBucket
                Resource: arn:aws:s3:::hjgshjsjhfjhdhvhkh

  # ── Instance Profile ───────────────────────────────────────
  EC2InstanceProfile:
    Type: AWS::IAM::InstanceProfile
    Properties:
      InstanceProfileName: EC2S3ListInstanceProfile
      Roles:
        - !Ref EC2S3Role

  # ── Networking ─────────────────────────────────────────────
  MyVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: MyVPC

  MyInternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: MyIGW

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref MyVPC
      InternetGatewayId: !Ref MyInternetGateway

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select
        - 0
        - !GetAZs ''

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.2.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select
        - 1
        - !GetAZs ''

  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref MyVPC
      Tags:
        - Key: Name
          Value: PublicRT

  DefaultRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref MyInternetGateway

  SubnetRouteTableAssociation1:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet1
      RouteTableId: !Ref PublicRouteTable

  SubnetRouteTableAssociation2:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet2
      RouteTableId: !Ref PublicRouteTable

  MySecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow SSH and HTTP
      VpcId: !Ref MyVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0   # ⚠️ Restrict to your IP in production
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  # ── EC2 Instance ───────────────────────────────────────────
  MyEC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.micro
      ImageId: !Ref LatestAmazonLinuxAMI
      SubnetId: !Ref PublicSubnet1
      SecurityGroupIds:
        - !Ref MySecurityGroup
      KeyName: lab
      IamInstanceProfile: !Ref EC2InstanceProfile
      UserData: !Base64
        Fn::Sub: |
          #!/bin/bash
          yum update -y
          yum install -y nginx
          systemctl start nginx
          systemctl enable nginx
          echo "ec2-user:${Password}" | chpasswd
          sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
          sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' /etc/ssh/sshd_config
          sed -i 's/PermitRootLogin no/PermitRootLogin yes/g' /etc/ssh/sshd_config
          systemctl restart sshd

# ========================
# OUTPUTS
# ========================
Outputs:
  InstancePublicIP:
    Description: EC2 Public IP
    Value: !GetAtt MyEC2Instance.PublicIp

  VPCId:
    Value: !Ref MyVPC

  SubnetId:
    Value: !Ref PublicSubnet1

  SSHCommand:
    Description: SSH command to connect
    Value: !Sub "ssh ec2-user@${MyEC2Instance.PublicIp}"

  S3BucketName:
    Description: S3 Bucket Name
    Value: !Ref MyS3Bucket

  EC2RoleName:
    Description: IAM Role attached to EC2
    Value: !Ref EC2S3Role
```

#### CFT Explanation — Resource by Resource

**Parameters**

| Parameter | Type | Purpose |
|---|---|---|
| `LatestAmazonLinuxAMI` | SSM dynamic lookup | Always fetches the latest AL2023 AMI ID automatically — no hardcoding |
| `Password` | `NoEcho: true` | Sets `ec2-user` password at launch; hidden from CloudFormation console logs |

**Networking Resources**

| Resource | Type | What It Does |
|---|---|---|
| `MyVPC` | `AWS::EC2::VPC` | Creates a VPC with CIDR `10.0.0.0/16`, DNS support and hostnames enabled |
| `MyInternetGateway` | `AWS::EC2::InternetGateway` | Creates an IGW — needed for public internet access |
| `AttachGateway` | `AWS::EC2::VPCGatewayAttachment` | Attaches the IGW to `MyVPC` |
| `PublicSubnet1` | `AWS::EC2::Subnet` | `10.0.1.0/24` in AZ index 0; `MapPublicIpOnLaunch: true` auto-assigns public IPs |
| `PublicSubnet2` | `AWS::EC2::Subnet` | `10.0.2.0/24` in AZ index 1; second subnet for redundancy |
| `PublicRouteTable` | `AWS::EC2::RouteTable` | Empty route table attached to the VPC |
| `DefaultRoute` | `AWS::EC2::Route` | Adds `0.0.0.0/0 → IGW` route; `DependsOn: AttachGateway` ensures IGW is attached first |
| `SubnetRouteTableAssociation1/2` | `AWS::EC2::SubnetRouteTableAssociation` | Links both public subnets to the route table so traffic can reach the IGW |

**IAM Resources**

| Resource | Type | What It Does |
|---|---|---|
| `MyS3Bucket` | `AWS::S3::Bucket` | Creates S3 bucket `hjgshjsjhfjhdhvhkh`; bucket name must be globally unique |
| `EC2S3Role` | `AWS::IAM::Role` | IAM Role with a trust policy allowing EC2 to assume it; inline policy grants only `s3:ListBucket` scoped to the specific bucket ARN |
| `EC2InstanceProfile` | `AWS::IAM::InstanceProfile` | Wrapper that allows an IAM Role to be attached to an EC2 instance; EC2 cannot use an IAM Role directly — it must go through an Instance Profile |

**EC2 Resources**

| Resource | Type | What It Does |
|---|---|---|
| `MySecurityGroup` | `AWS::EC2::SecurityGroup` | Allows inbound SSH (22) and HTTP (80) from anywhere |
| `MyEC2Instance` | `AWS::EC2::Instance` | `t3.micro` in `PublicSubnet1` with the IAM profile attached; UserData installs Nginx, sets password, enables SSH password auth |

**UserData Script (what runs at boot)**

```bash
yum update -y                          # Update all packages
yum install -y nginx                   # Install Nginx web server
systemctl start nginx                  # Start Nginx immediately
systemctl enable nginx                 # Enable Nginx to survive reboots
echo "ec2-user:${Password}" | chpasswd # Set password from CFT parameter
sed -i '...' /etc/ssh/sshd_config      # Enable SSH password authentication
systemctl restart sshd                 # Apply SSH config changes
```

**Verify S3 access from EC2:**
```bash
aws s3 ls s3://hjgshjsjhfjhdhvhkh     # ✅ Works — s3:ListBucket granted
aws s3 ls                              # ❌ Denied — s3:ListAllMyBuckets not granted
```

**CFT Resources Summary**

| Resource | Details |
|---|---|
| `MyVPC` | CIDR `10.0.0.0/16` |
| `MyS3Bucket` | `hjgshjsjhfjhdhvhkh` |
| `EC2S3Role` | `s3:ListBucket` on specific bucket ARN only |
| `EC2InstanceProfile` | Wraps `EC2S3Role` for attachment to EC2 |
| `MyEC2Instance` | `t3.micro`, public subnet, Nginx via UserData |
| `MySecurityGroup` | SSH (22), HTTP (80) open |

---

### Task 2 — Deploy VPC + Public EC2 + Private RDS MySQL via CloudFormation

**Objective:** Provision a production-style VPC with public EC2 and a fully private RDS MySQL instance. EC2 can reach RDS over port 3306; RDS is not internet-accessible. MySQL client installed on EC2 via UserData for direct DB connectivity testing.

#### CFT: `stack2-vpc-ec2-rds-mysql.json`

```json
{
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": "VPC with EC2 (public) and RDS MySQL (private)",
    "Parameters": {
        "LatestAmazonLinuxAMI": {
            "Type": "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
            "Default": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
        },
        "Password": {
            "Type": "String",
            "NoEcho": true,
            "Description": "Password for ec2-user",
            "MinLength": 8
        },
        "DBPassword": {
            "Type": "String",
            "NoEcho": true,
            "Description": "MySQL root password",
            "MinLength": 8
        }
    },
    "Resources": {
        "ProdVPC": {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": "192.168.0.0/16",
                "EnableDnsSupport": true,
                "EnableDnsHostnames": true,
                "Tags": [{ "Key": "Name", "Value": "ProdVPC" }]
            }
        },
        "ProdInternetGateway": {
            "Type": "AWS::EC2::InternetGateway",
            "Properties": {
                "Tags": [{ "Key": "Name", "Value": "ProdIGW" }]
            }
        },
        "AttachGateway": {
            "Type": "AWS::EC2::VPCGatewayAttachment",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "InternetGatewayId": { "Ref": "ProdInternetGateway" }
            }
        },
        "PublicSubnet1": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "CidrBlock": "192.168.1.0/24",
                "MapPublicIpOnLaunch": true,
                "AvailabilityZone": { "Fn::Select": [0, { "Fn::GetAZs": "" }] },
                "Tags": [{ "Key": "Name", "Value": "ProdPublicSubnet1" }]
            }
        },
        "PublicSubnet2": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "CidrBlock": "192.168.2.0/24",
                "MapPublicIpOnLaunch": true,
                "AvailabilityZone": { "Fn::Select": [1, { "Fn::GetAZs": "" }] },
                "Tags": [{ "Key": "Name", "Value": "ProdPublicSubnet2" }]
            }
        },
        "PrivateSubnet1": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "CidrBlock": "192.168.3.0/24",
                "MapPublicIpOnLaunch": false,
                "AvailabilityZone": { "Fn::Select": [0, { "Fn::GetAZs": "" }] },
                "Tags": [{ "Key": "Name", "Value": "ProdPrivateSubnet1" }]
            }
        },
        "PrivateSubnet2": {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "CidrBlock": "192.168.4.0/24",
                "MapPublicIpOnLaunch": false,
                "AvailabilityZone": { "Fn::Select": [1, { "Fn::GetAZs": "" }] },
                "Tags": [{ "Key": "Name", "Value": "ProdPrivateSubnet2" }]
            }
        },
        "PublicRouteTable": {
            "Type": "AWS::EC2::RouteTable",
            "Properties": {
                "VpcId": { "Ref": "ProdVPC" },
                "Tags": [{ "Key": "Name", "Value": "ProdPublicRT" }]
            }
        },
        "DefaultRoute": {
            "Type": "AWS::EC2::Route",
            "DependsOn": "AttachGateway",
            "Properties": {
                "RouteTableId": { "Ref": "PublicRouteTable" },
                "DestinationCidrBlock": "0.0.0.0/0",
                "GatewayId": { "Ref": "ProdInternetGateway" }
            }
        },
        "SubnetRouteTableAssociation1": {
            "Type": "AWS::EC2::SubnetRouteTableAssociation",
            "Properties": {
                "SubnetId": { "Ref": "PublicSubnet1" },
                "RouteTableId": { "Ref": "PublicRouteTable" }
            }
        },
        "SubnetRouteTableAssociation2": {
            "Type": "AWS::EC2::SubnetRouteTableAssociation",
            "Properties": {
                "SubnetId": { "Ref": "PublicSubnet2" },
                "RouteTableId": { "Ref": "PublicRouteTable" }
            }
        },
        "EC2SecurityGroup": {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Allow SSH and HTTP",
                "VpcId": { "Ref": "ProdVPC" },
                "SecurityGroupIngress": [
                    { "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "CidrIp": "0.0.0.0/0" },
                    { "IpProtocol": "tcp", "FromPort": 80, "ToPort": 80, "CidrIp": "0.0.0.0/0" }
                ],
                "Tags": [{ "Key": "Name", "Value": "EC2SG" }]
            }
        },
        "RDSSecurityGroup": {
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {
                "GroupDescription": "Allow MySQL only from EC2 security group",
                "VpcId": { "Ref": "ProdVPC" },
                "SecurityGroupIngress": [
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 3306,
                        "ToPort": 3306,
                        "SourceSecurityGroupId": { "Ref": "EC2SecurityGroup" }
                    }
                ],
                "Tags": [{ "Key": "Name", "Value": "RDSSG" }]
            }
        },
        "RDSSubnetGroup": {
            "Type": "AWS::RDS::DBSubnetGroup",
            "Properties": {
                "DBSubnetGroupDescription": "Private subnets for RDS",
                "SubnetIds": [
                    { "Ref": "PrivateSubnet1" },
                    { "Ref": "PrivateSubnet2" }
                ]
            }
        },
        "MyRDSInstance": {
            "Type": "AWS::RDS::DBInstance",
            "Properties": {
                "DBInstanceIdentifier": "prodmysqldb",
                "DBInstanceClass": "db.t3.micro",
                "Engine": "mysql",
                "EngineVersion": "8.0",
                "MasterUsername": "admin",
                "MasterUserPassword": { "Ref": "DBPassword" },
                "AllocatedStorage": 20,
                "StorageType": "gp2",
                "PubliclyAccessible": false,
                "MultiAZ": false,
                "DBSubnetGroupName": { "Ref": "RDSSubnetGroup" },
                "VPCSecurityGroups": [{ "Ref": "RDSSecurityGroup" }],
                "DeletionProtection": false
            }
        },
        "MyEC2Instance": {
            "Type": "AWS::EC2::Instance",
            "Properties": {
                "InstanceType": "t3.micro",
                "ImageId": { "Ref": "LatestAmazonLinuxAMI" },
                "SubnetId": { "Ref": "PublicSubnet1" },
                "SecurityGroupIds": [{ "Ref": "EC2SecurityGroup" }],
                "KeyName": "lab",
                "UserData": {
                    "Fn::Base64": {
                        "Fn::Sub": "#!/bin/bash\ndnf update -y\ndnf install -y nginx\nsystemctl start nginx\nsystemctl enable nginx\necho \"ec2-user:${Password}\" | chpasswd\nsed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config\nsed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' /etc/ssh/sshd_config\nsed -i 's/PermitRootLogin no/PermitRootLogin yes/g' /etc/ssh/sshd_config\nsystemctl restart sshd\ndnf install -y mariadb105\n"
                    }
                }
            }
        }
    },
    "Outputs": {
        "InstancePublicIP": {
            "Description": "EC2 Public IP",
            "Value": { "Fn::GetAtt": ["MyEC2Instance", "PublicIp"] }
        },
        "SSHCommand": {
            "Description": "SSH command to connect to EC2",
            "Value": { "Fn::Sub": "ssh ec2-user@${MyEC2Instance.PublicIp}" }
        },
        "RDSEndpoint": {
            "Description": "RDS MySQL endpoint",
            "Value": { "Fn::GetAtt": ["MyRDSInstance", "Endpoint.Address"] }
        },
        "MySQLConnectCommand": {
            "Description": "Run this on EC2 to connect to RDS",
            "Value": { "Fn::Sub": "mysql -h ${MyRDSInstance.Endpoint.Address} -u admin -p" }
        },
        "VPCId": {
            "Value": { "Ref": "ProdVPC" }
        }
    }
}
```

#### CFT Explanation — Resource by Resource

**Parameters**

| Parameter | Type | Purpose |
|---|---|---|
| `LatestAmazonLinuxAMI` | SSM dynamic lookup | Auto-fetches latest AL2023 AMI |
| `Password` | `NoEcho: true` | EC2 `ec2-user` login password |
| `DBPassword` | `NoEcho: true` | RDS MySQL `admin` user password — hidden from console |

**Networking Resources**

| Resource | CIDR / Details | Purpose |
|---|---|---|
| `ProdVPC` | `192.168.0.0/16` | Main VPC; different CIDR from Stack 1 to avoid overlap |
| `ProdInternetGateway` | — | Internet access gateway for public subnets |
| `AttachGateway` | — | Attaches IGW to ProdVPC |
| `PublicSubnet1` | `192.168.1.0/24` AZ-0 | EC2 lives here; `MapPublicIpOnLaunch: true` |
| `PublicSubnet2` | `192.168.2.0/24` AZ-1 | Second public subnet for HA readiness |
| `PrivateSubnet1` | `192.168.3.0/24` AZ-0 | RDS primary; `MapPublicIpOnLaunch: false` — no public IP |
| `PrivateSubnet2` | `192.168.4.0/24` AZ-1 | RDS secondary; RDS requires subnets in **minimum 2 AZs** |
| `PublicRouteTable` | — | Route table for public subnets |
| `DefaultRoute` | `0.0.0.0/0 → IGW` | Routes all internet traffic from public subnets through IGW |
| `SubnetRouteTableAssociation1/2` | — | Associates both public subnets with the route table |

> **Note:** Private subnets have **no route table association** to the public route table — this is intentional. RDS has no internet route, keeping it fully isolated.

**Security Groups**

| Resource | Inbound Rules | Purpose |
|---|---|---|
| `EC2SecurityGroup` | Port 22 (SSH), Port 80 (HTTP) from `0.0.0.0/0` | Allows internet access to EC2 |
| `RDSSecurityGroup` | Port 3306 **only** from `EC2SecurityGroup` (SG-to-SG reference) | RDS only reachable from EC2, not from internet |

> **Key concept:** Using `SourceSecurityGroupId` instead of a CIDR means only instances with `EC2SecurityGroup` attached can reach RDS — even if EC2's IP changes.

**RDS-Specific Resources**

| Resource | Type | What It Does |
|---|---|---|
| `RDSSubnetGroup` | `AWS::RDS::DBSubnetGroup` | Groups `PrivateSubnet1` and `PrivateSubnet2` together; RDS **requires** a subnet group with subnets in at least 2 AZs even for single-AZ deployments |
| `MyRDSInstance` | `AWS::RDS::DBInstance` | MySQL 8.0 on `db.t3.micro`, 20 GB `gp2` storage, `PubliclyAccessible: false` keeps it private, `DeletionProtection: false` allows stack deletion |

**EC2 UserData Script (what runs at boot)**

```bash
dnf update -y                          # AL2023 uses dnf, not yum
dnf install -y nginx                   # Install Nginx
systemctl start nginx                  # Start Nginx
systemctl enable nginx                 # Auto-start on reboot
echo "ec2-user:${Password}" | chpasswd # Set password from CFT parameter
sed -i '...' /etc/ssh/sshd_config      # Enable SSH password auth
systemctl restart sshd                 # Apply SSH changes
dnf install -y mariadb105              # MySQL-compatible client for AL2023
```

> **Why `mariadb105` and not `mysql`?** Amazon Linux 2023 removed the `mysql` package. `mariadb105` is the correct MySQL-compatible client available via `dnf` on AL2023. It provides the `mysql` CLI command.

**Connect to RDS from EC2:**
```bash
mysql -h <RDSEndpoint> -u admin -p
# Enter DBPassword when prompted
```

**CFT Resources Summary**

| Resource | Details |
|---|---|
| `ProdVPC` | CIDR `192.168.0.0/16` |
| `PublicSubnet1/2` | `192.168.1-2.0/24` — EC2 lives here |
| `PrivateSubnet1/2` | `192.168.3-4.0/24` — RDS lives here, no internet route |
| `EC2SecurityGroup` | SSH (22), HTTP (80) open to internet |
| `RDSSecurityGroup` | Port 3306 from `EC2SecurityGroup` only |
| `RDSSubnetGroup` | Groups both private subnets for RDS |
| `MyRDSInstance` | MySQL 8.0, `db.t3.micro`, private, non-MultiAZ |
| `MyEC2Instance` | `t3.micro`, public subnet, Nginx + mariadb105 client |

---

## 🔑 Key Fixes & Learnings Today

| Issue Encountered | Root Cause | Fix Applied |
|---|---|---|
| `yum install mysql` fails on AL2023 | AL2023 uses `dnf`, not `yum`; `mysql` package removed | Use `dnf install -y mariadb105` |
| S3 bucket creation failed (stack rollback) | Bucket name `onetwothree456987` already taken globally | Rename bucket — S3 names are globally unique across all AWS accounts |
| `aws s3 ls` gave `AccessDenied` from EC2 | `s3:ListAllMyBuckets` was not granted — by design | Expected behaviour; only `s3:ListBucket` on the specific bucket was allowed |
| CloudFormation has no `AWS::S3::Object` resource | CFT does not support creating objects inside S3 natively | Use Lambda Custom Resource or EC2 UserData script to write files |
| `s3:ListAllMyBuckets` needs `Resource: "*"` | AWS enforces this — it is a service-level action, not bucket-level | Cannot scope to a specific bucket ARN; must use `"*"` |
| RDS stack failed without subnet group | `AWS::RDS::DBInstance` requires a `DBSubnetGroupName` | Created `AWS::RDS::DBSubnetGroup` with 2 private subnets across 2 AZs |

---

## 📝 Homework Tasks

---

### Homework Task 1 — CFT: Deploy EC2 + S3 + Scoped IAM Role via CloudFormation

**Goal:** Create a CloudFormation template that provisions a complete networking stack with an EC2 instance that has permission to list only a specific S3 bucket.

**Requirements:**
- VPC with CIDR, public subnet, Internet Gateway, and route table
- EC2 instance with Nginx installed via UserData
- S3 bucket created inside the same template
- IAM Role with `s3:ListBucket` scoped **only** to that specific bucket ARN
- IAM Instance Profile wrapping the role and attached to the EC2

**Verification commands (run from EC2):**
```bash
# Should succeed — s3:ListBucket granted on this specific bucket
aws s3 ls s3://<your-bucket-name>

# Should be denied — s3:ListAllMyBuckets not in the policy
aws s3 ls
```

**Deliverable:** Stack deployed successfully with all resources in CREATE_COMPLETE state.

---

### Homework Task 2 — CFT: Deploy Public EC2 + Private RDS MySQL via CloudFormation

**Goal:** Create a CloudFormation template that provisions a production-style network with a public EC2 instance and a completely private RDS MySQL database reachable only from EC2.

**Requirements:**
- VPC with both public subnets (EC2) and private subnets (RDS) across 2 AZs
- EC2 in public subnet with SSH, HTTP, and MySQL client (`mariadb105`) installed
- RDS MySQL 8.0 in private subnet (`PubliclyAccessible: false`)
- RDS Security Group allowing port 3306 **only** from EC2 Security Group (SG-to-SG rule)
- DB Subnet Group with both private subnets
- Outputs that print the SSH command and MySQL connect command

**Verification (run from EC2 after SSH):**
```bash
mysql -h <RDSEndpoint> -u admin -p
# Enter your DBPassword — should connect successfully
```

**Deliverable:** MySQL connection from EC2 to RDS established successfully.

---

### Homework Task 3 — Concepts to Review

| Concept | What to Understand |
|---|---|
| `s3:ListBucket` vs `s3:ListAllMyBuckets` | `ListBucket` = list objects inside one bucket (can be scoped to ARN). `ListAllMyBuckets` = list all buckets in account (must use `Resource: "*"`) |
| Why RDS needs a DB Subnet Group with 2 AZs | AWS requires subnets in at least 2 AZs for fault tolerance planning, even if `MultiAZ: false`. It is a hard service requirement |
| `yum` vs `dnf` on AL2023 | Amazon Linux 2023 replaced `yum` with `dnf` as the package manager. `yum` still works as an alias but `dnf` is preferred and some packages (like `mariadb105`) only appear with `dnf` |
| CloudFormation Custom Resources | When CFT lacks a native resource (e.g. `AWS::S3::Object`), you create a Lambda-backed Custom Resource. CFT calls the Lambda on create/update/delete to handle the operation |
| IAM Instance Profile vs IAM Role | An IAM **Role** defines permissions. An IAM **Instance Profile** is the container that delivers a Role to an EC2 instance. EC2 cannot directly use a Role — it must be wrapped in an Instance Profile |

---

*Date: March 18, 2026 | Region: ap-south-1*