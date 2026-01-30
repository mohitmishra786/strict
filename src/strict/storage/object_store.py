from contextlib import asynccontextmanager
import aioboto3
from strict.config import settings


class ObjectStore:
    """Async S3 Object Store."""

    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket = settings.s3_bucket_name
        self.endpoint = settings.s3_endpoint_url
        self.access_key = (
            settings.s3_access_key.get_secret_value()
            if settings.s3_access_key
            else None
        )
        self.secret_key = (
            settings.s3_secret_key.get_secret_value()
            if settings.s3_secret_key
            else None
        )

    @asynccontextmanager
    async def get_client(self):
        """Get async s3 client."""
        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            yield client

    async def upload(self, key: str, data: bytes) -> str:
        """Upload bytes to S3."""
        async with self.get_client() as client:
            await client.put_object(Bucket=self.bucket, Key=key, Body=data)
            return key

    async def download(self, key: str) -> bytes:
        """Download bytes from S3."""
        async with self.get_client() as client:
            response = await client.get_object(Bucket=self.bucket, Key=key)
            return await response["Body"].read()


object_store = ObjectStore()
