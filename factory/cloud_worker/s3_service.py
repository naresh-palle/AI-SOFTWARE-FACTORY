"""
AWS S3 Artifact Storage Service.
Packages project workspace archives and securely uploads build artifacts.
"""

import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from factory.core.config import settings
from factory.core.logger import logger
from factory.core.security import hash_string


class S3ArtifactService:
    """Manages workspace packaging and S3 artifact storage."""

    def __init__(
        self,
        bucket_name: str = settings.AWS_S3_ARTIFACTS_BUCKET,
        region: str = settings.AWS_REGION,
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.has_aws_creds = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)

    def package_workspace(self, project_id: str, workspace_dir: Path) -> Path:
        """Create a compressed .tar.gz archive of the project workspace."""
        artifacts_dir = settings.PROJECTS_STORAGE_DIR / "artifacts" / project_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = f"build_{project_id[:8]}_{timestamp}.tar.gz"
        archive_path = artifacts_dir / archive_name

        with tarfile.open(archive_path, "w:gz") as tar:
            for item in workspace_dir.iterdir():
                if item.name not in {".git", "node_modules", "__pycache__", ".venv"}:
                    tar.add(item, arcname=item.name)

        logger.info(f"S3ArtifactService: Packaged workspace {project_id} -> {archive_path.name}")
        return archive_path

    async def upload_artifact(
        self,
        project_id: str,
        archive_path: Path,
    ) -> Dict[str, Any]:
        """Upload archive to S3 bucket or fallback to local artifact store."""
        file_bytes = archive_path.read_bytes()
        sha256 = hash_string(file_bytes.decode("latin1", errors="ignore"))
        s3_key = f"artifacts/{project_id}/{archive_path.name}"

        if self.has_aws_creds:
            try:
                import boto3
                s3_client = boto3.client(
                    "s3",
                    region_name=self.region,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
                s3_client.upload_file(str(archive_path), self.bucket_name, s3_key)
                artifact_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
                logger.info(f"S3ArtifactService: Uploaded to AWS S3: {artifact_url}")
                return {
                    "provider": "aws_s3",
                    "bucket": self.bucket_name,
                    "key": s3_key,
                    "url": artifact_url,
                    "size_bytes": len(file_bytes),
                    "sha256": sha256,
                    "uploaded_at": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.warning(f"S3ArtifactService: S3 upload failed ({e}), using local artifact store.")

        # Local fallback store
        local_url = f"file://{archive_path.resolve()}"
        return {
            "provider": "local_store",
            "bucket": "local-fallback",
            "key": s3_key,
            "url": local_url,
            "size_bytes": len(file_bytes),
            "sha256": sha256,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
