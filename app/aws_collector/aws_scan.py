import boto3
from dotenv import load_dotenv

load_dotenv()

def test_connection():
  STS_client = boto3.client("sts")
  response = STS_client.get_caller_identity()
  print(response)
  print("---------------------")
  print(f"The Account is {response['Account']} and the response is {response['Arn']}")



if __name__ == "__main__":
  test_connection()

