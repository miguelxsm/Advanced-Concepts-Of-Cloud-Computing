#!/usr/bin/env python3
"""
Create an AWS Application Load Balancer (ALB) with two Target Groups:
- cluster1 → all t2.large instances
- cluster2 → all t2.micro instances
Automatically discovers subnets in the given VPC.
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

REGION = "us-east-1"
VPC_ID = "vpc-09e3cd495f3ccc275"
SECURITY_GROUPS = ["sg-083dd7f63cb1cb9e5"]
ALB_NAME = "lab01-alb"

ec2 = boto3.client("ec2", region_name=REGION)
elbv2 = boto3.client("elbv2", region_name=REGION)

# ---------------------- LAB INSTANCES ----------------------

def get_lab_instances():
    """Return LAB01 instances grouped by type"""
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Lab", "Values": ["LAB01"]},
            {"Name": "instance-state-name", "Values": ["running"]}
        ]
    )
    instances = {"t2.large": [], "t2.micro": []}
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            iid = instance["InstanceId"]
            itype = instance["InstanceType"]
            if itype in instances:
                instances[itype].append(iid)
    return instances

# ---------------------- SUBNETS ----------------------

def get_subnets_for_vpc(vpc_id, min_required=2):
    """Automatically fetch subnets for a given VPC"""
    response = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
    subnets_by_az = {}
    for subnet in response["Subnets"]:
        az = subnet["AvailabilityZone"]
        subnet_id = subnet["SubnetId"]
        if az not in subnets_by_az:
            subnets_by_az[az] = subnet_id
    chosen_subnets = list(subnets_by_az.values())[:min_required]
    if len(chosen_subnets) < min_required:
        raise Exception(f"Not enough subnets in VPC {vpc_id} (found {len(chosen_subnets)})")
    return chosen_subnets

# ---------------------- CLEANUP HELPERS ----------------------

def delete_target_group_if_exists(name):
    """Delete a Target Group if it exists"""
    try:
        tgs = elbv2.describe_target_groups(Names=[name])["TargetGroups"]
        for tg in tgs:
            arn = tg["TargetGroupArn"]
            print(f"Deleting existing Target Group {name}...")
            elbv2.delete_target_group(TargetGroupArn=arn)
            time.sleep(2)
    except ClientError as e:
        if "TargetGroupNotFound" not in str(e):
            raise

def delete_alb_if_exists(name):
    """Delete an ALB and its listeners if it exists"""
    try:
        lbs = elbv2.describe_load_balancers(Names=[name])["LoadBalancers"]
        for lb in lbs:
            lb_arn = lb["LoadBalancerArn"]
            print(f"Deleting existing ALB {name} and its listeners...")
            listeners = elbv2.describe_listeners(LoadBalancerArn=lb_arn)["Listeners"]
            for listener in listeners:
                elbv2.delete_listener(ListenerArn=listener["ListenerArn"])
            elbv2.delete_load_balancer(LoadBalancerArn=lb_arn)
            waiter = elbv2.get_waiter("load_balancers_deleted")
            waiter.wait(LoadBalancerArns=[lb_arn])
            time.sleep(2)
    except ClientError as e:
        if "LoadBalancerNotFound" not in str(e):
            raise

# ---------------------- TARGET GROUPS ----------------------

def create_target_group(name, vpc_id, health_path):
    """Create HTTP target group on port 8000 with correct health check"""
    tg = elbv2.create_target_group(
        Name=name,
        Protocol="HTTP",
        Port=8000,
        VpcId=vpc_id,
        HealthCheckProtocol="HTTP",
        HealthCheckPort="8000",
        HealthCheckEnabled=True,
        HealthCheckPath=health_path,
        TargetType="instance"
    )
    return tg["TargetGroups"][0]["TargetGroupArn"]

def register_targets(tg_arn, instance_ids):
    """Register EC2 instances into a target group"""
    if instance_ids:
        targets = [{"Id": iid} for iid in instance_ids]
        elbv2.register_targets(TargetGroupArn=tg_arn, Targets=targets)

# ---------------------- ALB ----------------------

def create_alb(name, subnets, sg_ids):
    """Create the ALB"""
    lb = elbv2.create_load_balancer(
        Name=name,
        Subnets=subnets,
        SecurityGroups=sg_ids,
        Scheme="internet-facing",
        Type="application",
        IpAddressType="ipv4"
    )
    return lb["LoadBalancers"][0]

def create_listener(lb_arn, tg1_arn, tg2_arn):
    """Create a listener with forward rules for /cluster1 and /cluster2"""
    listener = elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol="HTTP",
        Port=80,
        DefaultActions=[{
            "Type": "forward",
            "ForwardConfig": {
                "TargetGroups": [
                    {"TargetGroupArn": tg1_arn, "Weight": 1},
                    {"TargetGroupArn": tg2_arn, "Weight": 1}
                ]
            }
        }]
    )
    listener_arn = listener["Listeners"][0]["ListenerArn"]

    # Add path-based rules
    elbv2.create_rule(
        ListenerArn=listener_arn,
        Priority=10,
        Conditions=[{"Field": "path-pattern", "Values": ["/cluster1*"]}],
        Actions=[{"Type": "forward", "TargetGroupArn": tg1_arn}]
    )

    elbv2.create_rule(
        ListenerArn=listener_arn,
        Priority=20,
        Conditions=[{"Field": "path-pattern", "Values": ["/cluster2*"]}],
        Actions=[{"Type": "forward", "TargetGroupArn": tg2_arn}]
    )

# ---------------------- MAIN ----------------------

def alb_and_tgs_exist(alb_name, tg_names):
    """Check if ALB and all required Target Groups exist."""
    alb_exists = False
    tg_exist = {name: False for name in tg_names}

    try:
        lbs = elbv2.describe_load_balancers(Names=[alb_name])["LoadBalancers"]
        if lbs:
            alb_exists = True
    except ClientError as e:
        if "LoadBalancerNotFound" not in str(e):
            raise

    for name in tg_names:
        try:
            tgs = elbv2.describe_target_groups(Names=[name])["TargetGroups"]
            if tgs:
                tg_exist[name] = True
        except ClientError as e:
            if "TargetGroupNotFound" not in str(e):
                raise

    return alb_exists, tg_exist

def main():
    print("🔎 Getting running LAB01 instances...")
    instances = get_lab_instances()
    print(f"  t2.large: {instances['t2.large']}")
    print(f"  t2.micro: {instances['t2.micro']}")

    tg_names = ["cluster1-tg", "cluster2-tg"]
    alb_exists, tg_exist = alb_and_tgs_exist(ALB_NAME, tg_names)

    if alb_exists and all(tg_exist.values()):
        print("✅ ALB and Target Groups already exist. Skipping creation.")
        return
    else:
        print("⚠️ ALB/Target Groups missing. Re-creating all...")

    delete_alb_if_exists(ALB_NAME)
    delete_target_group_if_exists("cluster1-tg")
    delete_target_group_if_exists("cluster2-tg")

    print("🌍 Discovering subnets automatically...")
    subnets = get_subnets_for_vpc(VPC_ID, min_required=2)
    print(f"   Using subnets: {subnets}")

    print("🌐 Creating target groups...")
    tg1_arn = create_target_group("cluster1-tg", VPC_ID, health_path="/cluster1")
    tg2_arn = create_target_group("cluster2-tg", VPC_ID, health_path="/cluster2")

    print("🔗 Registering instances...")
    register_targets(tg1_arn, instances["t2.large"])
    register_targets(tg2_arn, instances["t2.micro"])

    print("⚖️ Creating ALB...")
    lb = create_alb(ALB_NAME, subnets, SECURITY_GROUPS)
    lb_arn = lb["LoadBalancerArn"]
    dns = lb["DNSName"]

    print("🎧 Creating listener and rules...")
    create_listener(lb_arn, tg1_arn, tg2_arn)

    alb_info = {
        "LoadBalancerName": ALB_NAME,
        "LoadBalancerArn": lb_arn,
        "LoadBalancerFullName": lb["LoadBalancerName"],
        "DNSName": dns,
        "TargetGroup1": tg1_arn,
        "TargetGroup2": tg2_arn
    }
    with open("alb_info.json", "w") as f:
        json.dump(alb_info, f, indent=2)

    print("\n✅ ALB created successfully!")
    print(f"   Name: {ALB_NAME}")
    print(f"   DNS: {dns}")
    print("   Info saved in alb_info.json")

if __name__ == "__main__":
    main()
