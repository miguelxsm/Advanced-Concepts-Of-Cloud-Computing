import boto3

ec2 = boto3.resource("ec2", region_name="us-east-1")  # change region if needed

def create_security_group():
    sg_name = "lab01-security-group"
    vpc_id = "vpc-08afba995b983b2c4"
    
    # Check if the security group already already exists before creating it
    try:
        for sg in ec2.security_groups.all():
            if sg.group_name == sg_name:
                return
    except Exception as e:
        print("Error while checking SG:", e)

    # Create security group  
    response = ec2.create_security_group(
        GroupName=sg_name,
        Description="Security group for lab01 in LOG8415E",
        VpcId=vpc_id  # replace with your default VPC ID
    )

    security_group_id = response["GroupId"]
    print("Created security group:", security_group_id)

    # Add inbound rules
    ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]  # or better: just your IP
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 8000,
                "ToPort": 8000,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            }
        ]
    )


def create_instance():
    instances = ec2.create_instances(
        ImageId="ami-00ca32bbc84273381",   # Amazon Linux 2 AMI (for us-east-1, update if in another region)
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",          # or t2.large for your lab
        KeyName="LOG8415_key",             # replace with your key pair name
        SecurityGroupIds=["lab01-security-group"]
        # SecurityGroupIds=["sg-xxxxxxxx"], # replace with a Security Group that allows SSH (port 22) + HTTP (port 8000)
        # TagSpecifications=[
        #     {
        #         "ResourceType": "instance",
        #         "Tags": [{"Key": "Name", "Value": "MyLabInstance"}]
        #     }
        # ]
    )

    instance = instances[0]
    print("Launching instance... ID:", instance.id)
    instance.wait_until_running()
    instance.reload()
    print("Instance is running at Public IP:", instance.public_ip_address)

if __name__ == "__main__":
    create_security_group()
    create_instance()
