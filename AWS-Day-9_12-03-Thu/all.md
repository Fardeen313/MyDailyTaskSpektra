# AWS Lambda — Serverless Tasks

---

## Task 1 : Create a Serverless API with Lambda

### Objective
- Develop a Lambda function
- Trigger it using API Gateway
- Validate all API requests via CloudWatch Logs
- Test API requests using Postman

---

### Architecture

```
User / Postman
      │
      ▼
API Gateway (REST API)
  ├── GET  /dev  ──────────────────────────────────────┐
  └── POST /dev  ─────────────────────────────────────►│
                                                        │
                                               Lambda Function
                                                (Python 3.x)
                                                        │
                                          ┌─────────────┴─────────────┐
                                          ▼                           ▼
                                    Returns index.html         Inserts record into
                                    (Registration Form)        DynamoDB → returns
                                                               success.html
                                          │
                                          ▼
                                   CloudWatch Logs
                                  (All API requests logged)
```

---

### IAM Role Permissions Given to Lambda

| Permission | Purpose |
|---|---|
| `AmazonDynamoDBFullAccess` | Insert records into DynamoDB table |
| `CloudWatchLogsFullAccess` | Write invocation logs |
| `AmazonS3FullAccess` | Access HTML files stored in S3 |
| `AmazonAPIGatewayInvokeFullAccess` | Allow API Gateway to invoke Lambda |

---

### Lambda Function — `lambda_function.py`

```python
import json
import os
import boto3

def lambda_handler(event, context):
    try:
        mypage = page_router(
            event['httpMethod'],
            event['queryStringParameters'],
            event['body']
        )
        return mypage
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def page_router(httpmethod, querystring, formbody):
    if httpmethod == 'GET':
        try:
            with open('index.html', 'r') as htmlFile:
                htmlContent = htmlFile.read()
            return {
                'statusCode': 200,
                'headers': {"Content-Type": "text/html"},
                'body': htmlContent
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

    elif httpmethod == 'POST':
        try:
            insert_record(formbody)
            with open('success.html', 'r') as htmlFile:
                htmlContent = htmlFile.read()
            return {
                'statusCode': 200,
                'headers': {"Content-Type": "text/html"},
                'body': htmlContent
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

def insert_record(formbody):
    formbody = formbody.replace("=", "' : '")
    formbody = formbody.replace("&", "', '")
    formbody = "INSERT INTO mytable value {'" + formbody + "'}"
    client = boto3.client('dynamodb')
    response = client.execute_statement(Statement=formbody)
    return response
```

---

### `index.html` — Registration Form (Uploaded to Lambda)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contact Form</title>
  <style>
    body {
      font-family: 'Arial', sans-serif;
      background-color: #f4f4f4;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100vh;
      background-image: url('https://media.istockphoto.com/id/1367728715/vector/devops-concept-with-infinite-loop-on-abstract-technology-background.jpg?s=612x612&w=0&k=20&c=aadwZ3TQPv31Qxd_RyCwvoNNHBT1kNiaoksHtPdfKAA=');
      background-repeat: no-repeat;
      background-size: 100%;
    }
    form {
      background-color: #fff;
      padding: 20px;
      border-radius: 25px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      border-style: groove;
      border-color: rgb(9, 205, 9);
      width: 45%;
      transition: transform 0.3s ease-in-out;
    }
    h1 {
      text-align: center;
      color: #c81414;
      margin-bottom: 20px;
      background-color: rgb(244, 250, 154);
      font-family: unset;
    }
    h2 {
      text-align: center;
      color: #128de5;
      margin-bottom: 20px;
      font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
    }
    label {
      display: block;
      margin: 10px 0 5px;
      color: #555;
      font-size: larger;
      font-family: cursive;
    }
    input, textarea {
      width: 100%;
      padding: 10px;
      margin-bottom: 10px;
      box-sizing: border-box;
      border: 1px solid #ccc;
      border-radius: 15px;
      border-color: aqua;
    }
    input[type="submit"] {
      background-color: #a7386c;
      color: #fff;
      cursor: pointer;
      font-size: 16px;
      text-align: center;
    }
    input[type="submit"]:hover {
      background-color: #45a049;
    }
    form:hover {
      transform: scale(1);
      border-style: groove;
      border-color: gold;
    }
    footer {
      margin-top: 20px;
      font-size: 18px;
      text-align: center;
      color: rgb(16, 238, 116);
    }
  </style>
</head>
<body>
  <h1>Welcome to Multicloud with Devops by VEERA NareshIT</h1>
  <form action="/dev" method="post">
    <h2>MultiCloud devops Registration</h2>
    <label for="fname" style="color: red;">First Name:</label>
    <input type="text" id="fname" name="fname" required>
    <label for="lname" style="color: rgb(14, 46, 188);">Last Name:</label>
    <input type="text" id="lname" name="lname" required>
    <label for="email" style="color: rgb(225, 19, 204);">Email ID:</label>
    <input type="text" id="email" name="email" required>
    <label for="message" style="color: rgb(209, 153, 10);">Message:</label>
    <textarea id="message" name="message" rows="4" cols="50" required></textarea>
    <div style="text-align: center;">
      <input style="width: 250px;" type="submit" value="Submit">
    </div>
  </form>
  <footer>Multicloud with devops by VEERA</footer>
  <script>
    const form = document.querySelector('form');
    form.addEventListener('mouseover', () => {
      form.style.transform = 'scale(1.05)';
    });
    form.addEventListener('mouseout', () => {
      form.style.transform = 'scale(1)';
    });
  </script>
</body>
</html>
```

---

### `success.html` — Post-Submission Page (Uploaded to Lambda)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thank You</title>
  <style>
    body {
      font-family: 'Arial', sans-serif;
      background-color: #f4f4f4;
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background-image: url('data:image/png;base64,...');
      background-size: 99%;
      background-repeat: no-repeat;
    }
    h2 {
      text-align: center;
      color: #2200ff;
      padding: 20px;
      background-color: #fafafa;
      border-radius: 8px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;
    }
    .visible {
      opacity: 1;
      transform: translateY(0);
    }
  </style>
</head>
<body>
  <h2 id="thankYouMessage">
    You have uploaded details successfully. We will check and confirm your seat.
  </h2>
  <script>
    const thankYouMessage = document.getElementById('thankYouMessage');
    setTimeout(() => {
      thankYouMessage.classList.add('visible');
    }, 500);
  </script>
</body>
</html>
```

---

### API Gateway Setup

| Setting | Value |
|---|---|
| API Type | REST API |
| Methods | GET, POST |
| Integration | Lambda Proxy Integration ✅ |
| Stage Name | `dev` |
| CORS | Enabled ✅ |
| Invoke URL | `https://<api-id>.execute-api.<region>.amazonaws.com/dev` |

---

### Result

| Validation | Status |
|---|---|
| Accessed registration form via Invoke URL | ✅ |
| Form submission inserted records into DynamoDB | ✅ |
| CloudWatch Logs captured all GET and POST requests | ✅ |
| Postman GET request returned HTML form | ✅ |
| Postman POST request inserted record and returned success page | ✅ |

---
---

## Task 2 : Lambda Trigger on S3 PutObject — Auto Rename File

### Objective
Create a Lambda function that automatically **renames any object uploaded to a specific S3 bucket** by prepending a timestamp to the filename.

---

### Architecture

```
User uploads file to S3 Bucket
              │
              ▼  PutObject Event triggers
       Lambda Function
       (Python 3.x)
              │
              ▼
  Copies object with new name:
  YYYYMMDDHHMMSS_originalfilename
              │
              ▼
  Deletes original object
              │
              ▼
  CloudWatch Logs: prints original and renamed filename
```

---

### Setup Steps

| Step | Action |
|---|---|
| 1 | Created Lambda function with Python runtime |
| 2 | Attached IAM Role with `AmazonS3FullAccess` |
| 3 | Created S3 Bucket Policy to allow Lambda incoming requests |
| 4 | Added S3 Event Notification → trigger Lambda on `s3:ObjectCreated:Put` |
| 5 | Tested by uploading files — Lambda renamed them with timestamp prefix |

---

### Lambda Function — `lambda_function.py`

```python
import boto3
import urllib.parse
from datetime import datetime

s3 = boto3.client('s3')

def lambda_handler(event, context):

    # Get bucket name and object key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])

    print("Original file:", key)

    # Generate timestamp prefix
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Build new filename
    new_name = f"{timestamp}_{key}"

    # Copy object with new name
    s3.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': key},
        Key=new_name
    )

    # Delete original object
    s3.delete_object(Bucket=bucket, Key=key)

    print("Renamed file:", new_name)
```

---

### How the Rename Works

| Original Filename | Renamed Filename |
|---|---|
| `photo.jpg` | `20250318143022_photo.jpg` |
| `report.pdf` | `20250318143055_report.pdf` |
| `data.csv` | `20250318143101_data.csv` |

---

### Result

| Validation | Status |
|---|---|
| Lambda triggered on every S3 PutObject event | ✅ |
| Object copied with timestamp prefix | ✅ |
| Original object deleted after rename | ✅ |
| CloudWatch Logs printed original and new filename | ✅ |