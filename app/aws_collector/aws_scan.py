import boto3
from dotenv import load_dotenv

load_dotenv()

def test_connection():
  STS_client = boto3.client("sts")
  response = STS_client.get_caller_identity()
  print(response)
  print("---------------------")
  print(f"The Account is {response['Account']} and the response is {response['Arn']}")


def get_name(tags):
  for tag in Tags:
    if tag['Key'] == 'Name':
      return tag['Value']
  return "(no name)"


def list_instances():
  ec2 = boto3.client("ec2")
  response = ec2.describe_instances()
  region = ec2.meta.region_name
  found = 0

  for reservation in response['Reservations']:
    for instance in reservation['Instances']:
      name = get_name(instance.get('Tags', []))
      print(f"{instance['InstanceId']} | {instance['State']['Name']} | {instance['InstanceType']} | {name} | {region}")
      found += 1

  if found == 0:
    print(f"No EC2 instances found in {region}")


print("---------------------")
print(list_instances())




if __name__ == "__main__":
  test_connection()

