# Nested CloudFormation Stack — Production Infrastructure

---

## File Structure

```
nested-cft-project/
│
├── parent-main-stack.yaml          ← Root stack — deploys all nested stacks
│
├── nested-network-stack.yaml       ← Stack 1: VPC, Subnets, IGW, NGW, Route Tables, SG
├── nested-compute-stack.yaml       ← Stack 2: Launch Template, ASG, Target Group, IAM/SSM
├── nested-alb-stack.yaml           ← Stack 3: ALB, Listener, ALB Security Group
└── nested-s3-static-stack.yaml     ← Stack 4: S3 Static Website + Bucket Policy
```

---

## Architecture Overview

```
Internet
   │
   ▼
[ALB] (prod-app-alb)
   │  → placed in PublicSubnet1 (AZ-0) + PublicSubnet2 (AZ-1)
   │
   ▼
[Target Group] (prod-app-tg)  ← HTTP :80, health check on /
   │
   ▼
[Auto Scaling Group] (prod-app-asg)
   │  → launches EC2 instances in PrivateSubnet1 (AZ-0)
   │  → uses Launch Template with SSM role attached
   │
   ▼
[NAT Gateway] (prod-nat-gateway)
   │  → zonal, placed in PublicSubnet1
   │  → private subnet routes 0.0.0.0/0 → NGW → internet
   │
[S3 Static Website] (separate, no VPC dependency)
```

**Subnet Layout**

| Subnet | CIDR | AZ | Type | Connects to |
|---|---|---|---|---|
| `prod-public-subnet-1` | `10.0.1.0/24` | AZ-0 | Public | IGW, NAT GW lives here |
| `prod-public-subnet-2` | `10.0.2.0/24` | AZ-1 | Public | IGW |
| `prod-private-subnet-1` | `10.0.3.0/24` | AZ-0 | Private | NAT GW (same AZ) |

---

## How to Deploy

### Step 1 — Upload nested templates to S3

```bash
aws s3 mb s3://my-cft-templates-bucket

aws s3 cp nested-network-stack.yaml   s3://my-cft-templates-bucket/nested/
aws s3 cp nested-compute-stack.yaml   s3://my-cft-templates-bucket/nested/
aws s3 cp nested-alb-stack.yaml       s3://my-cft-templates-bucket/nested/
aws s3 cp nested-s3-static-stack.yaml s3://my-cft-templates-bucket/nested/
```

### Step 2 — Deploy parent stack

```bash
aws cloudformation deploy \
  --template-file parent-main-stack.yaml \
  --stack-name prod-main-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    TemplatesBucketURL=https://s3.amazonaws.com/my-cft-templates-bucket/nested \
    KeyName=your-keypair-name \
    StaticWebsiteBucketName=your-unique-bucket-name \
    ASGDesiredCapacity=2
```

### Step 3 — Delete (reverse order is handled automatically)

```bash
aws cloudformation delete-stack --stack-name prod-main-stack
```

---

## Stack 1 — `nested-network-stack.yaml`

**Purpose:** Foundation layer. All other stacks consume outputs from this stack.

### Resources

| Resource | CFT Type | Details |
|---|---|---|
| `VPC` | `AWS::EC2::VPC` | CIDR `10.0.0.0/16`, DNS support + hostnames enabled |
| `InternetGateway` | `AWS::EC2::InternetGateway` | Provides internet access to public subnets |
| `AttachInternetGateway` | `AWS::EC2::VPCGatewayAttachment` | Attaches IGW to VPC |
| `PublicSubnet1` | `AWS::EC2::Subnet` | `10.0.1.0/24`, AZ-0, `MapPublicIpOnLaunch: true` |
| `PublicSubnet2` | `AWS::EC2::Subnet` | `10.0.2.0/24`, AZ-1, different AZ from Subnet1 |
| `PrivateSubnet1` | `AWS::EC2::Subnet` | `10.0.3.0/24`, AZ-0 (same AZ as PublicSubnet1 — zonal NGW) |
| `NatGatewayEIP` | `AWS::EC2::EIP` | Elastic IP allocated for the NAT Gateway |
| `NatGateway` | `AWS::EC2::NatGateway` | Zonal NAT Gateway placed in `PublicSubnet1` |
| `PublicRouteTable` | `AWS::EC2::RouteTable` | Public RT — routes `0.0.0.0/0 → IGW` |
| `PublicDefaultRoute` | `AWS::EC2::Route` | Default route to IGW |
| `PublicSubnet1RouteTableAssociation` | `AWS::EC2::SubnetRouteTableAssociation` | Associates PublicSubnet1 with public RT |
| `PublicSubnet2RouteTableAssociation` | `AWS::EC2::SubnetRouteTableAssociation` | Associates PublicSubnet2 with public RT |
| `PrivateRouteTable` | `AWS::EC2::RouteTable` | Private RT — routes `0.0.0.0/0 → NAT Gateway` |
| `PrivateDefaultRoute` | `AWS::EC2::Route` | Default route to NGW for outbound internet |
| `PrivateSubnet1RouteTableAssociation` | `AWS::EC2::SubnetRouteTableAssociation` | Associates PrivateSubnet1 with private RT |
| `CommonSecurityGroup` | `AWS::EC2::SecurityGroup` | SSH (22) + HTTP (80) open from `0.0.0.0/0` |

### Outputs (consumed by parent + sibling stacks)

| Output | Value | Used By |
|---|---|---|
| `VpcId` | VPC resource ID | Compute Stack, ALB Stack |
| `PublicSubnet1Id` | Public Subnet 1 ID | ALB Stack |
| `PublicSubnet2Id` | Public Subnet 2 ID | ALB Stack |
| `PrivateSubnet1Id` | Private Subnet 1 ID | Compute Stack |
| `CommonSecurityGroupId` | SG ID | Compute Stack |

---

## Stack 2 — `nested-compute-stack.yaml`

**Purpose:** Application compute layer. Instances run in private subnet, reached only through the ALB.

### Parameters (received from parent via Network Stack outputs)

| Parameter | Source |
|---|---|
| `AmiId` | Parent parameter → passed in |
| `InstanceType` | Parent parameter |
| `KeyName` | Parent parameter |
| `VpcId` | `NetworkStack.Outputs.VpcId` |
| `PrivateSubnet1Id` | `NetworkStack.Outputs.PrivateSubnet1Id` |
| `CommonSecurityGroupId` | `NetworkStack.Outputs.CommonSecurityGroupId` |

### Resources

| Resource | CFT Type | Details |
|---|---|---|
| `EC2SSMRole` | `AWS::IAM::Role` | Attaches `AmazonSSMManagedInstanceCore` managed policy — enables Session Manager, Patch Manager, Run Command |
| `EC2InstanceProfile` | `AWS::IAM::InstanceProfile` | Wraps the IAM Role for attachment to EC2 |
| `AppTargetGroup` | `AWS::ElasticLoadBalancingV2::TargetGroup` | HTTP port 80, health check on `/`, `TargetType: instance` |
| `AppLaunchTemplate` | `AWS::EC2::LaunchTemplate` | AMI, instance type, key pair, SG, IAM profile, UserData (Nginx + SSM agent) |
| `AppAutoScalingGroup` | `AWS::AutoScaling::AutoScalingGroup` | Uses launch template, deploys in `PrivateSubnet1`, registers with Target Group |

### Key Design Points

- **IAM Role uses managed policy** `AmazonSSMManagedInstanceCore` — this allows SSH-less access via AWS Systems Manager Session Manager, no inbound port 22 needed for management
- **ASG Health Check type** is `ELB` — instances are replaced if they fail ALB health checks, not just EC2 status checks
- **Launch Template version** uses `!GetAtt AppLaunchTemplate.LatestVersionNumber` — ASG always uses the latest version automatically

### Outputs

| Output | Used By |
|---|---|
| `TargetGroupArn` | ALB Stack — attached to the HTTP Listener |
| `AutoScalingGroupName` | Parent Stack Outputs |

---

## Stack 3 — `nested-alb-stack.yaml`

**Purpose:** Traffic entry point. Distributes HTTP requests across ASG instances via the shared Target Group.

### Parameters (received from parent)

| Parameter | Source |
|---|---|
| `VpcId` | `NetworkStack.Outputs.VpcId` |
| `PublicSubnet1Id` | `NetworkStack.Outputs.PublicSubnet1Id` |
| `PublicSubnet2Id` | `NetworkStack.Outputs.PublicSubnet2Id` |
| `TargetGroupArn` | `ComputeStack.Outputs.TargetGroupArn` |

### Resources

| Resource | CFT Type | Details |
|---|---|---|
| `ALBSecurityGroup` | `AWS::EC2::SecurityGroup` | HTTP (80) + HTTPS (443) open from `0.0.0.0/0` — separate SG from EC2 instances |
| `AppLoadBalancer` | `AWS::ElasticLoadBalancingV2::LoadBalancer` | `internet-facing`, `application` type, spans both public subnets |
| `ALBHTTPListener` | `AWS::ElasticLoadBalancingV2::Listener` | HTTP :80 → forwards to `TargetGroupArn` from Compute Stack |

### Key Design Points

- ALB has its **own dedicated Security Group** (`prod-alb-sg`) separate from the EC2 instances
- ALB spans **both public subnets** in different AZs — required for ALB high availability
- The Target Group is created in the **Compute Stack**, not here — this is intentional so the ASG can register with it before the ALB listener is attached

### Outputs

| Output | Used By |
|---|---|
| `ALBDNSName` | Parent Stack Outputs — access URL |

---

## Stack 4 — `nested-s3-static-stack.yaml`

**Purpose:** Independent static website hosting — no VPC dependency.

### Resources

| Resource | CFT Type | Details |
|---|---|---|
| `StaticWebsiteBucket` | `AWS::S3::Bucket` | Static website hosting enabled, `IndexDocument: index.html`, `ErrorDocument: error.html`, all public block settings `false` |
| `StaticWebsiteBucketPolicy` | `AWS::S3::BucketPolicy` | `s3:GetObject` allowed for `Principal: '*'` on all objects — enables public HTTP access |

### Key Design Points

- `PublicAccessBlockConfiguration` must have all 4 settings set to `false` — otherwise the bucket policy allowing public access will be blocked by the account-level setting
- `WebsiteURL` attribute (`!GetAtt StaticWebsiteBucket.WebsiteURL`) returns the actual HTTP endpoint, not the S3 REST API endpoint

### Outputs

| Output | Value |
|---|---|
| `StaticWebsiteURL` | `http://<bucket>.s3-website-<region>.amazonaws.com` |

---

## Parent Stack — `parent-main-stack.yaml`

**Purpose:** Single entry point that wires all 4 nested stacks together, passing outputs of one as inputs to another.

### Dependency Chain

```
NetworkStack
     │
     ├── ComputeStack  (needs VpcId, PrivateSubnet1Id, CommonSGId from Network)
     │        │
     │        └── ALBStack  (needs VpcId, PublicSubnet1/2Id from Network + TargetGroupArn from Compute)
     │
     └── S3StaticStack  (independent — no network dependency)
```

### Parameter Flow

```
Parent Parameters
    AmiId ──────────────────────────────────► ComputeStack
    InstanceType ───────────────────────────► ComputeStack
    KeyName ────────────────────────────────► ComputeStack
    ASGMinSize / MaxSize / Desired ─────────► ComputeStack
    StaticWebsiteBucketName ────────────────► S3StaticStack

NetworkStack Outputs
    VpcId ──────────────────────────────────► ComputeStack, ALBStack
    PublicSubnet1Id / PublicSubnet2Id ──────► ALBStack
    PrivateSubnet1Id ───────────────────────► ComputeStack
    CommonSecurityGroupId ──────────────────► ComputeStack

ComputeStack Outputs
    TargetGroupArn ─────────────────────────► ALBStack
```

---

## Key Learnings

| Concept | Explanation |
|---|---|
| Nested stacks pass data via `Parameters` and `Outputs` | Parent uses `!GetAtt NestedStackName.Outputs.OutputKey` to read a child stack's output and pass it as a parameter to another child |
| `DependsOn` in parent stack | Ensures stacks are created in order: Network → Compute → ALB. S3 has no dependency |
| NAT Gateway must be zonal | One NGW placed in PublicSubnet1 (AZ-0); PrivateSubnet1 is in the same AZ-0 to avoid cross-AZ data transfer charges |
| Target Group created in Compute Stack, not ALB Stack | ASG must register instances with the TG. If TG were in ALB Stack, a circular dependency would form |
| ALB needs 2 subnets in different AZs | AWS requirement for Application Load Balancers — single-AZ ALB deployment is not allowed |
| `CAPABILITY_NAMED_IAM` required | Because the Compute Stack creates a named IAM Role and Instance Profile |

---

*Nested CFT Project | Region: ap-south-1*