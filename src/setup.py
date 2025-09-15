import boto3

# Resource is a high-level API
# Client is a low-level API
region = "us-east-1"
ec2_resource = boto3.resource("ec2", region_name=region)
ec2_client = boto3.client("ec2", region_name=region)
sg_name = "lab01-security-group"

def get_n_created_lab_instances():
    response = ec2_client.describe_instances()
    lab_instance_tag = {"Key": "Lab", "Value": "LAB01"}
    
    count = 0
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            if "Tags" in instance.keys() and lab_instance_tag in instance["Tags"]:
                count += 1

    return count

def security_group_exists(sg_name):
    exists = False
    try:
        response = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [sg_name]}]
        )
        if len(response["SecurityGroups"]) != 0:
            exists = True
    except Exception as e:
        print("Error while checking if security group exists: ", e)
    
    return exists

def create_security_group():
    vpc_id = "vpc-08afba995b983b2c4"
    
    # Check if the security group already already exists before creating it
    if security_group_exists(sg_name):
        return

    # Create security group  
    security_group = ec2_client.create_security_group(
        GroupName=sg_name,
        Description="Security group for lab01 in LOG8415E",
        VpcId=vpc_id
    )
    print("Security group creation started. Security group id: ", security_group["GroupId"])

    # Wait for security group to be created before adding rules
    group_waiter = ec2_client.get_waiter('security_group_exists')
    group_waiter.wait(GroupNames=[sg_name])
    print("Security group creation finished")

    # Add inbound rules
    ec2_client.authorize_security_group_ingress(
        GroupName=sg_name,
        GroupId=security_group["GroupId"],
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 8000,
                "ToPort": 8000,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            },
            {
                'FromPort': 80,
                'ToPort': 80,
                'IpProtocol': 'tcp',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
        ]
    )


def create_instance(instance_type: str, setup_script):
    instances = ec2_resource.create_instances(
        ImageId="ami-00ca32bbc84273381",   # Amazon Linux 2 AMI (for us-east-1)
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        KeyName="LOG8415_key",
        SecurityGroupIds=[sg_name],
        UserData=setup_script,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Lab", "Value": "LAB01"}]
            }
        ]
    )

    instance = instances[0]
    instance.wait_until_running()
    instance.reload()
    print("Instance is running at Public IP:", instance.public_ip_address)

def setup():
    instances_config = [
        {
            "type": "t2.micro",
            "setup_script": "user_data/cluster1.sh", 
        },
        {
            "type": "t2.large",
            "setup_script": "user_data/cluster2.sh", 
        }
    ]
    n_instances_by_type = 1
    n_necessary_instances = 8

    n_existing_instances = get_n_created_lab_instances()
    if n_existing_instances == n_necessary_instances:
        # TODO: just start instances
        print("STARTING INSTANCES")
    elif n_existing_instances == 0:
        # Create instances
        for instance_config in instances_config:
            setup_script = open(instance_config["setup_script"]).read()
            for _ in range(n_instances_by_type):
                create_instance(instance_config["type"], setup_script)
        print("All instances are created and running.")
    else:
        raise Exception(f"Unexpected number of instances found: {n_existing_instances} ... Stoping script.")


if __name__ == "__main__":
    create_security_group()
    setup()
