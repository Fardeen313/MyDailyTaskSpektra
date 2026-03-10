#!/bin/bash -xe
dnf yum update -y
sleep 60
dnf update -y
dnf install -y docker
systemctl enable docker
systemctl start docker
systemctl restart docker
systemctl status docker
groupadd docker
chmod 666 /var/run/docker.sock
usermod -aG docker ec2-user
docker pull fardeenattar/mario-image:20251104044029
docker run -d -p 8080:80 --name mario-container-01 fardeenattar/mario-image:20251104044029