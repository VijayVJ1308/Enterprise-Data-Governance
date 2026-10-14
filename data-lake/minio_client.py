import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("MinIOClient")


class MinIOClient:
    """
    MinIO S3 Object Storage Client Interface.
    Manages buckets: 'bronze-lake', 'silver-lake', 'gold-lake'.
    Falls back gracefully to local filesystem storage if MinIO service is unreachable.
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin_password",
        secure: bool = False,
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.buckets = ["bronze-lake", "silver-lake", "gold-lake"]
        self._minio_available = False
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from minio import Minio
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            # Check connection
            self._client.list_buckets()
            self._minio_available = True
            logger.info(f"Connected to MinIO server at {self.endpoint}")
            self._ensure_buckets()
        except Exception:
            logger.info("MinIO server not reachable locally. Operating in local filesystem lake mode.")
            self._minio_available = False

    def _ensure_buckets(self):
        if not self._minio_available or not self._client:
            return
        for bucket in self.buckets:
            try:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: '{bucket}'")
            except Exception as e:
                logger.warning(f"Could not create bucket '{bucket}': {e}")

    def upload_file(self, bucket_name: str, object_name: str, file_path: str) -> str:
        if self._minio_available and self._client:
            try:
                self._client.fput_object(bucket_name, object_name, file_path)
                return f"minio://{bucket_name}/{object_name}"
            except Exception as e:
                logger.warning(f"MinIO upload failed: {e}. Falling back to local lake path.")

        # Local fallback path
        local_target = os.path.join("data", "lake", bucket_name.replace("-lake", ""), object_name)
        os.makedirs(os.path.dirname(local_target), exist_ok=True)
        if file_path != local_target and os.path.exists(file_path):
            import shutil
            shutil.copy2(file_path, local_target)
        return local_target

    def list_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        if self._minio_available and self._client:
            try:
                objects = self._client.list_objects(bucket_name, prefix=prefix, recursive=True)
                return [obj.object_name for obj in objects]
            except Exception as e:
                logger.warning(f"MinIO list_objects failed: {e}")

        local_dir = os.path.join("data", "lake", bucket_name.replace("-lake", ""), prefix)
        if not os.path.exists(local_dir):
            return []
        found = []
        for root, _, files in os.walk(local_dir):
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), local_dir)
                found.append(rel)
        return found
