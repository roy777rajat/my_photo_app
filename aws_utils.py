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
    s3_client = None
    dynamodb_table = None

    try:
        session = boto3.Session(region_name=AWS_REGION)
        s3_client = session.client('s3')
        print("AWS Utils: S3 client initialized.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"AWS Utils ERROR: S3 - Credentials not found or incomplete. Error: {e}")
        # We can't proceed without S3, so re-raise or handle as critical
        raise Exception(f"S3 Client Initialization Failed: {e}")
    except ClientError as e:
        print(f"AWS Utils ERROR: S3 - Client error during initialization: {e}")
        raise Exception(f"S3 Client Initialization Failed: {e}")
    except Exception as e:
        print(f"AWS Utils ERROR: S3 - Unexpected error during initialization: {e}")
        raise Exception(f"S3 Client Initialization Failed: {e}")

    try:
        dynamodb_resource = session.resource('dynamodb')
        dynamodb_table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)
        
        # Test if table exists by trying a describe_table operation (cheap)
        # This will raise ResourceNotFoundException if the table is truly missing.
        dynamodb_table.table_status 
        
        print(f"AWS Utils: DynamoDB table '{DYNAMODB_TABLE_NAME}' initialized successfully.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"AWS Utils ERROR: DynamoDB - Credentials not found or incomplete. Error: {e}")
        # This is critical for DynamoDB too, so re-raise
        raise Exception(f"DynamoDB Client Initialization Failed: {e}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'AuthFailure':
            print(f"AWS Utils ERROR: DynamoDB - Authentication failed. Check credentials/region. Error: {e}")
            raise Exception(f"DynamoDB Auth Failure: {e}") # Critical, re-raise
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"AWS Utils WARNING: DynamoDB table '{DYNAMODB_TABLE_NAME}' not found. DynamoDB functionality will be unavailable. Error: {e}")
            dynamodb_table = None # This is the key: return None if not found
        else:
            print(f"AWS Utils ERROR: DynamoDB - An unexpected ClientError occurred: {e}")
            raise # Re-raise other unexpected ClientErrors
    except Exception as e:
        print(f"AWS Utils ERROR: DynamoDB - General error during initialization: {e}")
        raise # Re-raise other general errors

    return s3_client, dynamodb_table # Always return both, s3_client will be valid, dynamodb_table might be None


# --- Ensure dependent functions can handle dynamodb_table being None ---

def upload_file_to_s3(s3_client, uploaded_file):
    """Uploads a file object to S3 and returns the S3 key and public URL."""
    if not s3_client: # Add this check
        print("Error: S3 client not initialized. Cannot upload file.")
        return None, None
    try:
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}" # Generate a unique filename
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=unique_filename,
            Body=uploaded_file.getvalue(),
            ContentType=uploaded_file.type # Set content type for proper display
        )
        
        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
        
        return unique_filename, public_url
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None, None

def save_metadata_to_dynamodb(dynamodb_table, photo_id, s3_key, s3_url, description, original_filename, uploader="anonymous"):
    """Saves photo metadata to DynamoDB."""
    if not dynamodb_table: # Add this check
        print("ERROR: DynamoDB table is not available. Cannot save metadata.")
        return False
    try:
        t = int(datetime.datetime.now().timestamp() * 1000)
        photo_id = photo_id + str(t) # Ensure photo_id is unique by appending timestamp
        dynamodb_table.put_item(
            Item={
                'photo_id': photo_id,
                's3_key': s3_key, # Store the S3 key for later retrieval
                's3_url': s3_url,
                'description': description,
                'original_filename': original_filename,
                'uploader': uploader,
                'upload_timestamp': t # Milliseconds since epoch
            }
        )
        return True
    except Exception as e:
        print(f"Error saving metadata to DynamoDB: {e}")
        return False

def get_photos_from_dynamodb(dynamodb_table):
    """Retrieves all photo metadata from DynamoDB."""
    if not dynamodb_table: # Add this check
        print("ERROR: DynamoDB table is not available. Cannot retrieve photos.")
        return []
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
    if not s3_client: # Add this check
        print("Error: S3 client not initialized. Cannot get S3 object data.")
        return None
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return response['Body'].read()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"Object with key {s3_key} not found in S3 bucket {S3_BUCKET_NAME}.")
            return None
        print(f"Error getting object from S3: {e}")
        return None