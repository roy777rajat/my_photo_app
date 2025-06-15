# my_photo_app/aws_utils.py

import boto3
import uuid
import datetime
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Import configuration from config.py
from .config import S3_BUCKET_NAME, DYNAMODB_TABLE_NAME, AWS_REGION

# Initialize AWS clients (use session state in app.py for caching)
def get_aws_clients():
    """Initializes and returns Boto3 S3 client and DynamoDB table resource."""
    try:
        session = boto3.Session(region_name=AWS_REGION)
        s3_client = session.client('s3')
        dynamodb_resource = session.resource('dynamodb')
        dynamodb_table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
        return s3_client, dynamodb_table
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise Exception(f"AWS credentials not found or incomplete. Please configure your AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION environment variables or IAM role. Error: {e}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AuthFailure':
            raise Exception(f"AWS authentication failed. Check your credentials and region. Error: {e}")
        raise e # Re-raise other ClientErrors

def upload_file_to_s3(s3_client, uploaded_file):
    """Uploads a file object to S3 and returns the S3 key and public URL."""
    try:
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}" # Generate a unique filename
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=unique_filename,
            Body=uploaded_file.getvalue(),
            ContentType=uploaded_file.type # Set content type for proper display
        )
        
        # Construct the public URL (assuming public read access is configured on S3)
        # For private buckets, you would generate a pre-signed URL here.
        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        
        return unique_filename, public_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None, None

def save_metadata_to_dynamodb(dynamodb_table, photo_id, s3_key, s3_url, description, original_filename, uploader="anonymous"):
    """Saves photo metadata to DynamoDB."""
    try:
        dynamodb_table.put_item(
            Item={
                'photo_id': photo_id,
                's3_key': s3_key, # Store the S3 key for later retrieval
                's3_url': s3_url,
                'description': description,
                'original_filename': original_filename,
                'uploader': uploader,
                'upload_timestamp': int(datetime.datetime.now().timestamp() * 1000) # Milliseconds since epoch
            }
        )
        return True
    except Exception as e:
        print(f"Error saving metadata to DynamoDB: {e}")
        return False

def get_photos_from_dynamodb(dynamodb_table):
    """Retrieves all photo metadata from DynamoDB."""
    try:
        response = dynamodb_table.scan()
        photos = response['Items']
        # Sort by timestamp in descending order (most recent first)
        photos.sort(key=lambda x: x.get('upload_timestamp', 0), reverse=True)
        return photos
    except Exception as e:
        print(f"Error retrieving photos from DynamoDB: {e}")
        return []

def get_s3_object_data(s3_client, s3_key):
    """Fetches image data from S3 for zipping."""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"Object with key {s3_key} not found in S3 bucket {S3_BUCKET_NAME}.")
            return None
        print(f"Error getting object from S3: {e}")
        return None