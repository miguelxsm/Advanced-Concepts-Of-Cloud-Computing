import boto3

# Resource is a high-level API
# Client is a low-level API
ec2_resource = boto3.resource("ec2", region_name="us-east-1")
ec2_client = boto3.client("ec2", region_name="us-east-1")
sg_name = "lab01-security-group"

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
        VpcId=vpc_id  # replace with your default VPC ID
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


def create_instance():
    instances = ec2_resource.create_instances(
        ImageId="ami-00ca32bbc84273381",   # Amazon Linux 2 AMI (for us-east-1, update if in another region)
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",          # or t2.large for your lab
        KeyName="LOG8415_key",             # replace with your key pair name
        SecurityGroupIds=[sg_name],
        # SecurityGroupIds=["sg-xxxxxxxx"], # replace with a Security Group that allows SSH (port 22) + HTTP (port 8000)
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Lab", "Value": "LAB01"}]
            }
        ]
    )

    instance = instances[0]
    print("Launching instance... ID:", instance.id)
    instance.wait_until_running()
    instance.reload()
    print("Instance is running at Public IP:", instance.public_ip_address)

if __name__ == "__main__":
    create_security_group()
    create_instance()
