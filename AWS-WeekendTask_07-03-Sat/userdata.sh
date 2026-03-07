#!/bin/bash

dnf update -y

dnf install -y unzip curl

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

mkdir -p /home/ec2-user/dockerconfig123

aws s3 cp s3://dockerconfig123/dockerconfig123/docker.sh /home/ec2-user/dockerconfig123/docker.sh

chmod +x /home/ec2-user/dockerconfig123/docker.sh

sh /home/ec2-user/dockerconfig123/docker.sh

mkdir -p /var/log/docker
touch /var/log/docker/mario.log
chmod 666 /var/log/docker/mario.log

docker logs -f mario-container >> /var/log/docker/mario.log 2>&1 &

yum install -y amazon-cloudwatch-agent

cat <<EOF > /opt/aws/amazon-cloudwatch-agent/bin/config.json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/docker/mario.log",
            "log_group_name": "docker-mario-logs",
            "log_stream_name": "{instance_id}",
            "retention_in_days": 1
          }
        ]
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
-a fetch-config \
-m ec2 \
-c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json \
-s

cat <<EOF > /usr/local/bin/dockerlogupload.sh
#!/bin/bash
aws s3 cp /var/log/docker/mario.log s3://dockerconfig123/applog/mario-\$(date +%F-%H-%M).log
EOF

chmod +x /usr/local/bin/dockerlogupload.sh

(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/dockerlogupload.sh") | crontab -