#!/bin/bash -xe
sleep 10
echo "installing cw agent"
dnf install -y amazon-cloudwatch-agent
mkdir -p /home/ec2-user/dockerconfig123
echo "cli"
dnf install -y awscli
aws s3 cp s3://dockerconfig12345678/dockerconfig123/docker.sh /home/ec2-user/dockerconfig123/docker.sh
chmod 555 /home/ec2-user/dockerconfig123/docker.sh
echo "installing docker"
bash /home/ec2-user/dockerconfig123/docker.sh
echo "installed docker"


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
            "file_path": "/var/lib/docker/containers/*/*.log",
            "log_group_class": "STANDARD",
            "log_group_name": "Dockerapp",
            "log_stream_name": "{instance_id}-{container_id}",
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
dnf install -y cronie
systemctl start crond
systemctl enable crond
mkdir -p /var/log/docker-s3
cat <<'EOL' > /usr/local/bin/dockerlogupload.sh
#!/bin/bash
cp /var/lib/docker/containers/*/*.log /var/log/docker-s3/
for f in /var/log/docker-s3/*.log; do
    aws s3 cp "$f" s3://dockerconfig12345678/dockerconfig123/$(basename "$f")-$(date +%F-%H-%M).log
done
rm -f /var/log/docker-s3/*.log
EOL

chmod +x /usr/local/bin/dockerlogupload.sh
(crontab -l 2>/dev/null; echo "* * * * * /usr/local/bin/dockerlogupload.sh") | crontab -