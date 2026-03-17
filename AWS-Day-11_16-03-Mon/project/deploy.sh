#!/bin/bash
# deploy.sh — Apply all Kubernetes manifests in order

echo ">>> Applying Secrets..."
kubectl apply -f k8s/secret.yaml

echo ">>> Applying PersistentVolumeClaim..."
kubectl apply -f k8s/mysql-pvc.yaml

echo ">>> Deploying MySQL..."
kubectl apply -f k8s/mysql-deployment.yaml

echo ">>> Waiting for MySQL to be ready..."
kubectl wait --for=condition=ready pod -l app=mysql --timeout=120s

echo ">>> Deploying Flask App..."
kubectl apply -f k8s/flask-deployment.yaml

echo ""
echo "✅ All resources deployed!"
echo ""
echo ">>> Current pods:"
kubectl get pods

echo ""
echo ">>> Services:"
kubectl get services
