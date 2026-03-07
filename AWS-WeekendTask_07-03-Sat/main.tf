provider "aws" {
  region = "ap-south-1"
}

######################    AWS S3 Bucket     #####################################
resource "aws_s3_bucket" "docker_bucket" {
  bucket = var.bucket
}

#######################   AWS S3 File object (Config) #############################
resource "aws_s3_object" "upload_script" {
  bucket     = aws_s3_bucket.docker_bucket.id
  key        = "${var.bucket_key}/docker.sh"
  source     = "docker.sh"
  depends_on = [aws_s3_bucket.docker_bucket]
}

#######################   Data source to get AWS account ID ####################
data "aws_caller_identity" "current" {
}

#######################   AWS S3 Bucket Policy #############################
resource "aws_s3_bucket_policy" "docker_bucket_policy" {
  bucket     = aws_s3_bucket.docker_bucket.id
  depends_on = [aws_s3_bucket.docker_bucket]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEC2RolePutObject"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/EC2-CW-S3"
        }
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "arn:aws:s3:::${aws_s3_bucket.docker_bucket.id}/dockerconfig123/*"
      }
    ]
  })
}

#######################  Datasource to fetch existing IAM Role #####################
data "aws_iam_instance_profile" "myexisting_role" {
  name = "EC2-CW-S3"

}

######################   EC2 Instance with User Data and IAM Role ############################
resource "aws_instance" "my_ec2_instance" {
  ami                  = var.image
  instance_type        = var.instance_type
  key_name             = var.key
  iam_instance_profile = data.aws_iam_instance_profile.myexisting_role.name
  depends_on           = [aws_s3_object.upload_script]
  user_data            = file("userdata.sh")
  tags = {
    Name = "MyEC2Instance"
  }
}
output "public" {
  value = "${aws_instance.my_ec2_instance.public_ip}:8080"
}
output "name" {
  value = data.aws_iam_instance_profile.myexisting_role.id
}