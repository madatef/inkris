from uuid import UUID
from datetime import datetime, timedelta, timezone

import aioboto3
import boto3
from botocore.exceptions import ClientError

from app.storage.base import UploadSpec, StorageProvider
from app.config import settings


class S3StorageProvider(StorageProvider):
    def __init__(
        self,
        bucket_name: str,
        region_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        expiration_seconds: int = 600,
    ):
        """
        Initialize S3 storage provider.
        
        Args:
            bucket_name: S3 bucket name
            region_name: AWS region (optional, uses default if not specified)
            aws_access_key_id: AWS access key (optional, uses default credentials if not specified)
            aws_secret_access_key: AWS secret key (optional, uses default credentials if not specified)
            expiration_seconds: Presigned URL expiration time in seconds (default: 600/10 minutes)
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.expiration_seconds = expiration_seconds
        
        # Initialize S3 client
        session_kwargs = {
            "region_name": region_name,
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
        }
        self.client = boto3.client('s3', **session_kwargs)
    
    def create_presigned_upload(
        self,
        *,
        file_id: UUID,
        size_bytes: int,
        content_type: str,
    ) -> UploadSpec:
        """
        Create a presigned POST URL for uploading to S3.
        
        Args:
            file_id: Unique identifier for the file
            size_bytes: Size of the file in bytes
            content_type: MIME type of the file
            
        Returns:
            UploadSpec with presigned upload details
        
        Raises:
            RuntimeError: if S3 client failed to create the url
        """
        # Use file_id as the S3 object key
        object_key = str(file_id)
        
        # Prepare conditions for the presigned POST
        conditions = [
            {"bucket": self.bucket_name},
            {"acl": "private"},
            ["content-length-range", size_bytes, size_bytes],
            {"Content-Type": content_type},
            {"x-amz-server-side-encryption": "AES256"},
        ]
        
        fields = {
            "Content-Type": content_type,
            "acl": "private",
            "x-amz-server-side-encryption": "AES256",
        }
        try:
            # Generate presigned POST
            response = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=self.expiration_seconds,
            )
            
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=self.expiration_seconds)
            ).isoformat()
            
            return UploadSpec(
                method="POST",
                url=response["url"],
                headers=None,
                fields=response["fields"],
                expires_at=expires_at,
            )
            
        except ClientError as e:
            raise RuntimeError(f"Failed to create presigned upload URL: {e}")

    def create_presigned_download(
        self,
        *,
        file_id: UUID,
        expires_seconds: int = 300,
    ) -> str:
        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": str(file_id),
            },
            ExpiresIn=expires_seconds,
        )

    def get_object_url(
        self,
        *,
        key: str,
    ) -> str:
        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{key}"


# files storage
s3 = S3StorageProvider(
    bucket_name=settings.AWS_S3_BUCKET,
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    expiration_seconds=600,
)

# AI-generated media storgae
s3_media_client_session = aioboto3.Session(
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)
