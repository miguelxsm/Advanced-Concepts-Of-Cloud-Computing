#!/usr/bin/env python3
"""
Main orchestrator for the lab assignment.
Steps:
1. Create security group and EC2 instances (setup.py).
2. Create Application Load Balancer and Target Groups (create_alb.py).
3. Run benchmark against ALB (benchmark.py).
4. Fetch CloudWatch metrics and save to CSV (cloudwatch.py).
"""

import subprocess
import sys
import time
import boto3
import socket

region = "us-east-1"
ec2_client = boto3.client("ec2", region_name=region)

LAB_TAG = {"Key": "Lab", "Value": "LAB01"}

# ---------------------- MAIN ----------------------

def main():
    # Step 1: Create security group and instances
    run_step("Creating security group and instances", ["python3", "src/setup.py"])

    # Step 2: Create ALB and Target Groups
    run_step("Creating Application Load Balancer", ["python3", "src/create_alb.py"])

    # Step 3: Run benchmark
    run_step("Running benchmark", ["python3", "src/benchmark.py"])

    # Step 4: Fetch CloudWatch metrics
    #run_step("Fetching CloudWatch metrics", ["python3", "src/cloudwatch.py"])

    print("\n✅ Pipeline completed successfully!")

if __name__ == "__main__":
    main()
