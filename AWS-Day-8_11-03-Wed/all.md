# 📘 Day-8 Lab

## Topic: Static Website Hosting using Amazon S3 and Accessing via CloudFront CDN

---

## Table of Contents

1. [Objective](#objective)
2. [Amazon S3 Overview](#amazon-s3-simple-storage-service)
3. [AWS CloudFront Overview](#aws-cloudfront)
4. [Task: Host Static Website via S3 + CloudFront](#task-host-static-website-using-s3-and-access-via-cloudfront)
5. [CORS Configuration](#cors-configuration)
6. [CloudFront Cache Invalidation](#cloudfront-cache-invalidation)
7. [Architecture Summary](#architecture-summary)

---

## Objective

In this lab we explored **Amazon S3 and AWS CloudFront** and implemented a static website hosting architecture.

The lab includes:

- Understanding **Amazon S3 basics**
- Understanding **AWS CloudFront basics**
- Hosting a **static website using S3**
- Delivering the website using **CloudFront CDN**
- Configuring **CORS** for cross-origin resource sharing
- Performing **CloudFront Cache Invalidations**
- Accessing website content through **CloudFront DNS endpoint**

This architecture improves **performance, availability, and global delivery of web content**.

---

## Amazon S3 (Simple Storage Service)

Amazon S3 is an **object storage service** designed to store and retrieve any amount of data from anywhere on the internet.

It provides:

- High durability (99.999999999% — 11 nines)
- High availability
- Scalability
- Secure storage with fine-grained access control

### Common Use Cases

| Use Case | Description |
|---|---|
| Static Website Hosting | Hosting HTML/CSS/JS websites |
| Backup & Archival | Store backups and disaster recovery data |
| Data Lakes | Big data storage and analytics |
| Media Storage | Images, videos, files |
| Application Assets | Store application content and logs |

---

### S3 Core Components

#### Bucket

A **Bucket** is a top-level container used to store objects in S3.

```
my-static-website-bucket
```

Characteristics:
- Globally unique name across all AWS accounts
- Region specific (data stays in chosen region)
- Acts as the root namespace for all objects inside it

#### Objects

Objects are **files stored inside buckets**, along with their metadata.

```
index.html
style.css
script.js
image.png
```

Each object contains:
- **Data** — the actual file content
- **Metadata** — key-value pairs describing the object (Content-Type, size, etc.)
- **Unique Key** — the full path/name of the object within the bucket

#### Static Website Hosting

Amazon S3 can host static websites directly from a bucket. Supported content types:
- HTML, CSS, JavaScript, Images

When enabled, S3 generates a public **website endpoint URL**:

```
http://bucket-name.s3-website-region.amazonaws.com
```

---

## AWS CloudFront

**AWS CloudFront** is a global **Content Delivery Network (CDN)** that distributes content from AWS services to end users through a worldwide network of **edge locations**.

### Benefits

| Feature | Benefit |
|---|---|
| Global CDN | Faster website loading worldwide |
| Caching | Reduces origin (S3) load |
| HTTPS | Secure content delivery |
| Edge Locations | 400+ locations globally, low latency |
| DDoS Protection | Built-in AWS Shield Standard |
| Scalability | Handles massive traffic spikes |

### How CloudFront Works

```
User Request
      │
      ▼
Nearest CloudFront Edge Location
      │
      ├── Cache HIT  → Serve directly (fast ⚡)
      │
      └── Cache MISS → Fetch from S3 Origin → Cache → Serve
```

1. User sends a request to CloudFront
2. CloudFront routes to the nearest edge location
3. If cached → served directly (very fast)
4. If not cached → fetched from S3 origin, cached, then delivered
5. Subsequent requests are served from cache

---

## Task: Host Static Website using S3 and Access via CloudFront

### Architecture Overview

```
User Browser
      │
      ▼ HTTPS
CloudFront Distribution (d123abcd.cloudfront.net)
      │
      ▼ Origin fetch (on cache miss)
S3 Bucket (day28-static-site)
      │
      └── index.html, style.css, images/
```

---

### Step 1: Create an S3 Bucket

Navigate to:
> AWS Console → S3 → Create Bucket

| Setting | Value |
|---|---|
| Bucket Name | `day28-static-site` (must be globally unique) |
| Region | `us-east-1` (or your preferred region) |
| Block Public Access | **Disabled** (uncheck all 4 options) |
| Versioning | Optional |

---

### Step 2: Upload Website Files

Upload your static files to the bucket:

```
index.html
error.html
style.css
images/
```

Example `index.html`:

```html
<!DOCTYPE html>
<html>
  <head><title>Day-28 Static Website</title></head>
  <body>
    <h1>Welcome to Day-28 Static Website</h1>
    <p>Hosted using Amazon S3 and delivered via CloudFront CDN.</p>
  </body>
</html>
```

---

### Step 3: Enable Static Website Hosting

Navigate to:
> Bucket → Properties → Static Website Hosting → Enable

| Setting | Value |
|---|---|
| Hosting Type | Host a static website |
| Index Document | `index.html` |
| Error Document | `error.html` |

After saving, S3 generates a website endpoint:

```
http://day28-static-site.s3-website-us-east-1.amazonaws.com
```

---

### Step 4: Configure Bucket Policy (Public Read)

Navigate to:
> Bucket → Permissions → Bucket Policy

Add the following policy to allow public read access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::day28-static-site/*"
    }
  ]
}
```

---

### Step 5: Create CloudFront Distribution

Navigate to:
> AWS Console → CloudFront → Create Distribution

**Origin Settings:**

| Setting | Value |
|---|---|
| Origin Domain | S3 static website endpoint (NOT the bucket URL) |
| Origin Protocol | HTTP only (S3 website endpoints are HTTP) |
| Origin Path | Leave blank |

**Default Cache Behavior:**

| Setting | Value |
|---|---|
| Viewer Protocol Policy | Redirect HTTP to HTTPS |
| Allowed HTTP Methods | GET, HEAD |
| Cache Policy | CachingOptimized |
| Compress Objects | Yes |

**Distribution Settings:**

| Setting | Value |
|---|---|
| Price Class | Use all edge locations |
| Default Root Object | `index.html` |
| WAF | Optional |

Click **Create Distribution** — CloudFront generates a domain:

```
https://d123abcd.cloudfront.net
```

---

### Step 6: Wait for Deployment

CloudFront takes **5–10 minutes** to propagate globally.

Monitor status:
> CloudFront → Distributions → Status: **Deploying** → **Enabled** ✅

---

### Step 7: Access Website via CloudFront

Open in browser:

```
https://d123abcd.cloudfront.net
```

The website is now served through CloudFront CDN with HTTPS, caching, and global edge delivery.

---

## CORS Configuration

### What is CORS?

**Cross-Origin Resource Sharing (CORS)** is a browser security mechanism that controls how resources on one domain can be requested from another domain.

Without CORS, if your website at `https://d123abcd.cloudfront.net` tries to fetch a resource (font, JSON, image) from another origin, the browser **blocks the request**.

```
Browser
   │
   ├── Requests https://d123abcd.cloudfront.net/index.html   ✅ Same origin
   │
   └── Requests https://anotherdomain.com/data.json          ❌ Cross-origin → BLOCKED without CORS
```

### When do you need CORS on S3?

- Your website fetches **fonts, scripts, or JSON files** from S3 via JavaScript (`fetch`, `XMLHttpRequest`)
- Another domain's frontend calls your S3 bucket directly
- You use **multiple CloudFront distributions** pointing to the same S3 bucket
- Your frontend (CloudFront domain) loads assets from S3 directly

### Configure CORS on S3 Bucket

Navigate to:
> S3 → Bucket → Permissions → Cross-Origin Resource Sharing (CORS) → Edit

Add the following CORS configuration:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://d123abcd.cloudfront.net"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

**Configuration explained:**

| Field | Value | Meaning |
|---|---|---|
| `AllowedHeaders` | `*` | Allow all request headers |
| `AllowedMethods` | `GET, HEAD` | Read-only access |
| `AllowedOrigins` | CloudFront domain | Only this domain can make cross-origin requests |
| `ExposeHeaders` | `ETag` | Expose ETag header to browser for cache validation |
| `MaxAgeSeconds` | `3000` | Browser caches CORS preflight response for 50 minutes |

### Allow All Origins (Less Secure — Dev Only)

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3000
  }
]
```

> ⚠️ Use specific origins in production, never `*`

### Forward CORS Headers via CloudFront

For CORS to work properly end-to-end, CloudFront must **forward the `Origin` header** to S3. Otherwise CloudFront caches one response and ignores which origin made the request — causing CORS failures for some users.

Navigate to:
> CloudFront → Distribution → Behaviors → Edit → Cache Key and Origin Requests

Set **Origin Request Policy** to include the `Origin` header, or use the AWS managed policy:

```
Managed-CORS-S3Origin
```

This ensures CloudFront passes the browser's `Origin` header to S3, and S3 responds with the correct `Access-Control-Allow-Origin` header.

### CORS Request Flow

```
Browser (d123abcd.cloudfront.net)
      │
      │  OPTIONS preflight request
      │  Origin: https://d123abcd.cloudfront.net
      ▼
CloudFront (forwards Origin header)
      │
      ▼
S3 Bucket
      │  Checks CORS config
      │  Responds: Access-Control-Allow-Origin: https://d123abcd.cloudfront.net
      ▼
CloudFront (caches response with Origin in cache key)
      │
      ▼
Browser → CORS check passed ✅ → Proceeds with actual request
```

---

## CloudFront Cache Invalidation

### What is Cache Invalidation?

When you **update files in S3**, CloudFront continues serving the **old cached version** from edge locations until the cache TTL (Time To Live) expires — which could be hours or days.

**Cache Invalidation** forces CloudFront to **immediately purge** cached objects so fresh content is fetched from S3 on the next request.

```
You update index.html in S3
        │
        ▼
CloudFront edge still serves OLD index.html ❌ (still cached)
        │
        ▼  ← Create Invalidation
CloudFront purges cached index.html
        │
        ▼
Next request fetches NEW index.html from S3 ✅
        │
        ▼
Users see updated content ✅
```

### When to Invalidate?

| Scenario | Invalidation Path |
|---|---|
| Updated a specific HTML file | `/index.html` |
| Deployed new website version | `/*` |
| Fixed CSS bug in production | `/style.css` |
| Updated all images | `/images/*` |
| Changed everything | `/*` |

### How to Create an Invalidation (Console)

Navigate to:
> CloudFront → Distributions → Select Distribution → Invalidations tab → Create Invalidation

**Invalidate all files:**

```
/*
```

**Invalidate specific files:**

```
/index.html
/style.css
/images/logo.png
```

**Invalidate a folder:**

```
/images/*
```

Click **Create Invalidation** → Status changes from **In Progress** → **Completed** ✅

---

### Invalidation via AWS CLI

```bash
# Invalidate all files
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/*"

# Invalidate specific files
aws cloudfront create-invalidation \
    --distribution-id YOUR_DISTRIBUTION_ID \
    --paths "/index.html" "/style.css"

# Check invalidation status
aws cloudfront list-invalidations \
    --distribution-id YOUR_DISTRIBUTION_ID
```

---

### Invalidation Cost

| Tier | Cost |
|---|---|
| First 1,000 paths/month | **Free** |
| After 1,000 paths | $0.005 per path |

> 💡 **Tip:** Using `/*` counts as **1 path**, not one per file — always use wildcard for full deploys to save cost.

---

### Alternative to Invalidation — File Versioning

Instead of invalidating, use **versioned filenames** so CloudFront treats updated files as brand new objects — no invalidation needed:

```
# Old approach — requires invalidation
style.css  (updated) → must invalidate /style.css

# Versioned approach — no invalidation needed
style.v1.css → style.v2.css  (new object, CloudFront fetches automatically)
style.css?v=1748293847       (query string versioning)
```

Update your HTML to reference the new versioned filename, and CloudFront will automatically fetch the new file.

---

## Architecture Summary

```
User (Browser)
      │
      ▼ HTTPS Request
┌──────────────────────────────────┐
│    CloudFront Edge Location      │
│  (nearest to user globally)      │
│                                  │
│  Cache HIT  → Serve response ⚡  │
│  Cache MISS → Fetch from S3      │
│                                  │
│  Invalidation clears cache       │
│  CORS Origin header forwarded    │
└──────────────────────────────────┘
      │ Origin fetch (cache miss only)
      ▼
┌──────────────────────────────────┐
│         S3 Bucket                │
│    day28-static-site             │
│                                  │
│    index.html                    │
│    error.html                    │
│    style.css                     │
│    images/                       │
│                                  │
│    ✅ Static website hosting ON  │
│    ✅ Public bucket policy set   │
│    ✅ CORS configured            │
│    ✅ Block public access OFF    │
└──────────────────────────────────┘
```

---

## Task Completed Summary

| Step | Task | Status |
|---|---|---|
| 1 | Created S3 bucket with public access enabled | ✅ Done |
| 2 | Uploaded static website files (HTML, CSS, images) | ✅ Done |
| 3 | Enabled Static Website Hosting on S3 | ✅ Done |
| 4 | Configured bucket policy for public read | ✅ Done |
| 5 | Created CloudFront distribution with S3 as origin | ✅ Done |
| 6 | Configured HTTPS with redirect HTTP → HTTPS | ✅ Done |
| 7 | Configured CORS on S3 bucket | ✅ Done |
| 8 | Forwarded Origin header in CloudFront cache policy | ✅ Done |
| 9 | Performed cache invalidation after updating files | ✅ Done |
| 10 | Accessed website via CloudFront HTTPS endpoint | ✅ Done |

---

*Document generated for AWS learning lab — Day 28: S3 + CloudFront Static Website Hosting*