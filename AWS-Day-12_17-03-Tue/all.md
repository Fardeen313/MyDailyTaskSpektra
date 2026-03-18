# Deploy EC2 Instance with Complete Network Infrastructure, UserData Web Server & SSH Password Configuration using AWS CloudFormation
## What I Did

Deployed a complete AWS infrastructure using a CloudFormation Template (CFT) that provisions a VPC with all networking components, launches an EC2 instance, installs Nginx as a web server, and configures SSH to allow password-based login — all automated via UserData.

---

## Infrastructure Created via CFT

| Resource | Name | Details |
|---|---|---|
| VPC | MyVPC | CIDR: 10.0.0.0/16, DNS enabled |
| Internet Gateway | MyIGW | Attached to MyVPC |
| Public Subnet 1 | PublicSubnet1 | 10.0.1.0/24 — AZ-0 |
| Public Subnet 2 | PublicSubnet2 | 10.0.2.0/24 — AZ-1 |
| Route Table | PublicRT | 0.0.0.0/0 → IGW |
| RT Association 1 | SubnetRouteTableAssociation1 | PublicSubnet1 ↔ PublicRT |
| RT Association 2 | SubnetRouteTableAssociation2 | PublicSubnet2 ↔ PublicRT |
| Security Group | MySecurityGroup | Port 22 (SSH), Port 80 (HTTP) |
| EC2 Instance | MyEC2Instance | t3.micro, Amazon Linux 2023 |

---

## UserData — What Runs on Boot

```bash
#!/bin/bash
yum update -y
yum install -y nginx
systemctl start nginx
systemctl enable nginx

# Set password for ec2-user
echo "ec2-user:${Password}" | chpasswd

# Enable SSH password authentication
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin no/PermitRootLogin yes/g' /etc/ssh/sshd_config

systemctl restart sshd
```

---

## CFT Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: VPC with IGW, subnets, route table, SG, and EC2 with Nginx

Parameters:
  LatestAmazonLinuxAMI:
    Type: AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>
    Default: /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64

  Password:
    Type: String
    NoEcho: true
    Description: Password for ec2-user
    MinLength: 8

Resources:
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
      AvailabilityZone: !Select [0, !GetAZs '']

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref MyVPC
      CidrBlock: 10.0.2.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select [1, !GetAZs '']

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
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0

  MyEC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: t3.micro
      ImageId: !Ref LatestAmazonLinuxAMI
      SubnetId: !Ref PublicSubnet1
      SecurityGroupIds:
        - !Ref MySecurityGroup
      KeyName: lab
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
```

---

## Outputs

| Key | Value |
|---|---|
| `InstancePublicIP` | Public IP of EC2 |
| `VPCId` | VPC ID |
| `SubnetId` | PublicSubnet1 ID |
| `SSHCommand` | `ssh ec2-user@<public-ip>` |

---

## Verification

```bash
# Test Nginx
curl http://<InstancePublicIP>

# SSH with password
ssh ec2-user@<InstancePublicIP>
# enter password set during stack creation
```