import boto3

def list_ec2_instances(region="us-east-1"):
    ec2 = boto3.client("ec2", region_name=region)

    response = ec2.describe_instances()
    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append({
                "InstanceId": instance["InstanceId"],
                "State": instance["State"]["Name"],
                "Type": instance["InstanceType"],
                "AZ": instance["Placement"]["AvailabilityZone"],
                "PublicIP": instance.get("PublicIpAddress", "N/A")
            })

    if not instances:
        print("No EC2 instances found in region", region)
    else:
        print(f"Found {len(instances)} EC2 instance(s) in {region}:")
        for inst in instances:
            print(inst)

if __name__ == "__main__":
    list_ec2_instances("us-east-1")  # change region if needed
