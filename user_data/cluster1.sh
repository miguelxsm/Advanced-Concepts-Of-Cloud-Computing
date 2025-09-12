#!/bin/bash
set -e
# ===== Base packages =====
apt-get update -y
apt-get install -y python3 python3-pip git

# ===== 2) Clone repository =====
# Sustituye la URL por la tuya:
cd /home/ubuntu
if [ ! -d app ]; then
  git clone https://github.com/miguelxsm/Advanced-Concepts-Of-Cloud-Computing.git app
fi

# ===== Dependencies =====
pip3 install -r app/requirements.txt

# ===== 4) Defining Cluster =====
echo 'export CLUSTER_NAME=cluster1' > /etc/profile.d/cluster.sh # explain in the report how this helps
export CLUSTER_NAME=cluster1

# ===== 5) Deploy =====
cd /home/ubuntu/app
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 >/home/ubuntu/app.log 2>&1 &
