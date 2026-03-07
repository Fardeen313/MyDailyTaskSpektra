# AWS Overview and AWS Account Management Hierarchy

---

# 1. AWS Overview

Amazon Web Services (AWS) is a cloud computing platform that provides on‑demand infrastructure such as compute, storage, networking, databases, security, and many other services.

Instead of purchasing physical servers, organizations use AWS to:

* Launch servers on demand
* Store data securely
* Build scalable applications
* Pay only for what they use

AWS follows a **global infrastructure model** consisting of Regions, Availability Zones, and Edge locations.

---

# 2. AWS Account

An **AWS Account** is the basic container for all AWS resources.

When someone signs up for AWS using an email address, AWS creates:

* A **Root User**
* A **Standalone Account** (initially)

Every AWS resource such as EC2, S3, RDS, Lambda, etc., belongs to an AWS account.

---

# 3. Root User

The **Root User** is the original identity created when an AWS account is registered.

Characteristics:

* Has **full unrestricted access** to all AWS services
* Cannot be restricted using IAM policies
* Used only for **critical administrative tasks**

Examples of root user tasks:

* Changing account email
* Closing AWS account
* Modifying support plan
* Changing payment methods

Best practice:

Root user should **not be used for daily operations**.

---

# 4. Standalone Account

A **Standalone Account** is an AWS account that is **not part of AWS Organizations**.

Characteristics:

* Managed independently
* Has its own billing
* Uses only IAM for permissions
* Cannot use Service Control Policies (SCP)

When an AWS account is first created, it starts as a **Standalone Account**.

---

# 5. AWS Organizations

**AWS Organizations** is a service used to manage multiple AWS accounts centrally.

Organizations help companies:

* Manage multiple accounts easily
* Apply security policies
* Consolidate billing
* Group accounts logically

When an organization is created, the **Standalone Account becomes the Management Account**.

---

# 6. Promotion from Standalone Account to Management Account

When AWS Organizations is enabled, the existing standalone account is promoted to a **Management Account**.

Hierarchy representation:

```
Standalone Account (Initial AWS Account)
              │
              ▼
        Management Account
              │
      ┌───────┼──────────┐
      ▼       ▼          ▼
     OU-Dev  OU-Test   OU-Prod
      │       │          │
  ┌───┴───┐   │      ┌───┴───┐
  ▼       ▼   ▼      ▼       ▼
Member  Member Member  Member Member
Account Account Account Account Account
```

The **management account controls the entire organization**.

---

# 7. Management Account

The **Management Account** (previously called Master Account) is the central account that manages the AWS Organization.

Responsibilities:

* Create and manage AWS Organizations
* Manage billing for all accounts
* Create Organizational Units (OUs)
* Invite accounts
* Create new member accounts
* Apply Service Control Policies

There can be **only one management account per organization**.

---

# 8. Organizational Units (OU)

**Organizational Units (OUs)** are logical containers used to group AWS accounts.

Purpose:

* Apply policies to multiple accounts
* Organize accounts based on environment

Example:

```
Organization
   │
   ├── Dev OU
   │      ├── Dev Account 1
   │      └── Dev Account 2
   │
   ├── Test OU
   │      └── Test Account
   │
   └── Prod OU
          └── Production Account
```

This helps apply security and governance policies easily.

---

# 9. Member Accounts

**Member Accounts** are AWS accounts that belong to an AWS Organization.

Characteristics:

* Controlled by the management account
* Can be placed inside OUs
* Controlled using SCP policies
* Have their own IAM users and resources

---

# 10. Creating an Organization

Steps to create an AWS Organization:

1. Login using root or admin user
2. Open AWS Organizations service
3. Click **Create Organization**

Two types of organization modes:

* **All Features Mode** (Recommended)
* **Consolidated Billing Only**

All Features Mode allows:

* SCP
* Account creation
* Full governance

---

# 11. Creating Accounts Inside Organization

The management account can create new accounts.

Requirements:

* Unique email address
* Account name

When created, AWS automatically:

* Creates a new AWS account
* Makes it a **Member Account**
* Places it inside the organization

These accounts automatically share:

* Organization policies
* Billing under management account

---

# 12. Inviting Existing Accounts to Organization

The management account can **invite existing standalone accounts**.

Requirements:

* Account ID or email address
* Invitation must be accepted by that account

Supported accounts to invite:

* Standalone Accounts

Accounts that **cannot be invited**:

* Accounts already inside another organization

If an account is already a member of another organization:

1. The account must **leave the existing organization**
2. Then it becomes a **standalone account again**
3. After that it can be invited to a new organization

---

# 13. Service Control Policies (SCP)

**Service Control Policies (SCP)** define the maximum permissions available for accounts in an organization.

Important rule:

SCP **does NOT grant permissions**.

It only **limits what permissions IAM can grant**.

Example:

IAM Policy:

Allow EC2

SCP:

Deny EC2

Result:

Access denied.

---

# 14. SCP Levels

SCP can be applied at multiple hierarchy levels.

```
Organization Level
        │
        ▼
OU Level
        │
        ▼
Account Level
```

All SCP policies are evaluated together.

If any level denies an action → the action is denied.

---

# 15. IAM (Identity and Access Management)

IAM manages **users and permissions inside a single AWS account**.

Main components:

* IAM Users
* IAM Groups
* IAM Roles
* IAM Policies

IAM is used for **fine‑grained access control**.

---

# 16. IAM Users and Groups

### IAM User

An IAM user represents a person or application.

Each user may have:

* Console password
* Access keys
* Attached policies

### IAM Group

An IAM group is a collection of IAM users.

Example:

```
Developers Group
   ├── User1
   ├── User2
   └── User3
```

Permissions assigned to the group apply to all users.

---

# 17. AWS Billing and Cost Management Budgets

AWS provides **Budgets** to monitor and control cloud spending.

Budgets help organizations:

* Track spending
* Prevent unexpected costs
* Receive alerts when limits exceed

Types of AWS Budgets:

### 1. Cost Budget

Tracks **total AWS spending**.

Example:

Monthly limit = $100

If spending crosses $80 → alert is triggered.

---

### 2. Usage Budget

Tracks **service usage** instead of cost.

Example:

* EC2 hours
* S3 storage usage

---

### 3. Reservation Budget

Tracks **Reserved Instance utilization or coverage**.

Two metrics:

* Coverage
* Utilization

Example:

Ensures purchased reserved instances are actually used.

---

### 4. Savings Plans Budget

Tracks **Savings Plan utilization and coverage**.

Helps monitor whether savings plans are fully used.

---

# 18. Security Best Practices and Permission Priority

### Do NOT Use Root User

Reasons:

* Unlimited permissions
* Security risk
* No granular control

Best practice:

1. Enable MFA on root account
2. Create an **Admin IAM User**
3. Use admin user for daily work

---

### Permission Priority in IAM

AWS evaluates permissions using this rule:

```
Explicit Deny > Allow
```

Example:

User Policy → Allow S3

Group Policy → Deny S3

Final Result → **Denied**

---

### Permission Evaluation Across Organization

```
SCP (Organization Level)
        │
        ▼
SCP (OU Level)
        │
        ▼
SCP (Account Level)
        │
        ▼
IAM Policies (User / Group / Role)
```

Final rule:

Action is allowed **only if both conditions are true**:

1. SCP allows the action
2. IAM policy allows the action

If SCP denies → IAM cannot override it.

---

# End of Document
