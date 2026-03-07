#!/bin/bash

sudo dnf update -y
sudo dnf install docker -y

sudo systemctl start docker
sudo systemctl enable docker

sudo usermod -aG docker ec2-user

sudo docker pull fardeenattar/mario-image:20251104044029

sudo docker run -d -p 8080:80 --name mario-container fardeenattar/mario-image:20251104044029