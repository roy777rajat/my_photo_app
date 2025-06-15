# my_photo_app/config.py

# --- AWS S3 Configuration ---
S3_BUCKET_NAME = "my-family-photos-yourname-unique-bucket" # <<< REPLACE WITH YOUR S3 BUCKET NAME (must be globally unique!)

# --- AWS DynamoDB Configuration ---
DYNAMODB_TABLE_NAME = "FamilyPhotoMetadata" # <<< REPLACE WITH YOUR DYNAMODB TABLE NAME

# --- AWS Region ---
# Ensure this matches the region where your S3 bucket and DynamoDB table are created
AWS_REGION = "eu-west-2" # <<< REPLACE WITH YOUR AWS REGION (e.g., 'us-east-1', 'ap-southeast-2')