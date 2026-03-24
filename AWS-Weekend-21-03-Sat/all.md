# EC2 CloudFormation Lab Guide

Deploy an EC2 instance with an auto-fetched AMI and a new Key Pair using CloudFormation (JSON).

---

## Prerequisites

- AWS account with IAM permissions for EC2, CloudFormation, and SSM
- AWS CLI installed and configured (`aws configure`)
- A terminal / shell

---

## Step 1 — Save the Template

Save the provided JSON as `ec2-simple.json` on your local machine.

```bash
ls ec2-simple.json   # confirm the file is present
```

---

## Step 2 — Deploy the Stack

```bash
aws cloudformation create-stack \
  --stack-name my-ec2-lab \
  --template-body file://ec2-simple.json \
  --parameters \
      ParameterKey=InstanceType,ParameterValue=t3.micro \
      ParameterKey=KeyPairName,ParameterValue=my-lab-key \
      ParameterKey=SSHLocation,ParameterValue=0.0.0.0/0
```

> **Tip:** Replace `0.0.0.0/0` with your own IP (`curl ifconfig.me`) for better security.

---

## Step 3 — Wait for Stack Completion

```bash
aws cloudformation wait stack-create-complete \
  --stack-name my-ec2-lab

echo "Stack is ready!"
```

Takes ~2–3 minutes.

---

## Step 4 — Fetch Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name my-ec2-lab \
  --query "Stacks[0].Outputs" \
  --output table
```

Note down the **PublicIP** and **KeyPairId** from the output table.

---

## Step 5 — Download the Private Key

```bash
KEY_PAIR_ID=$(aws cloudformation describe-stacks \
  --stack-name my-ec2-lab \
  --query "Stacks[0].Outputs[?OutputKey=='KeyPairId'].OutputValue" \
  --output text)

aws ssm get-parameter \
  --name "/ec2/keypair/${KEY_PAIR_ID}" \
  --with-decryption \
  --query Parameter.Value \
  --output text > my-lab-key.pem

chmod 400 my-lab-key.pem
```

---

## Step 6 — SSH into the Instance

```bash
PUBLIC_IP=$(aws cloudformation describe-stacks \
  --stack-name my-ec2-lab \
  --query "Stacks[0].Outputs[?OutputKey=='PublicIP'].OutputValue" \
  --output text)

ssh -i my-lab-key.pem ec2-user@${PUBLIC_IP}
```

You should see the Amazon Linux 2 welcome banner.

---

## Step 7 — Cleanup

```bash
aws cloudformation delete-stack --stack-name my-ec2-lab

aws cloudformation wait stack-delete-complete --stack-name my-ec2-lab

echo "Stack deleted."
```

---

## What the Template Creates

| Resource | Purpose |
|---|---|
| `AWS::EC2::KeyPair` | New key pair; private key auto-saved to SSM |
| `AWS::EC2::SecurityGroup` | Allows SSH (port 22) inbound |
| `AWS::EC2::Instance` | Amazon Linux 2, AMI auto-fetched via SSM |

---

## Verify AMI Resolution (Optional)

To see which AMI was resolved for your region:

```bash
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2 \
  --query Parameter.Value \
  --output text
```