from typing import Optional

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from utils.config import sys_cfg


class S3ObjectStore:
    def __init__(self):
        self._s3 = boto3.client(
            's3',
            endpoint_url=sys_cfg.s3.url,
            aws_access_key_id=sys_cfg.s3.key_id,
            aws_secret_access_key=sys_cfg.s3.access_key
        )
        self._bucket = sys_cfg.s3.bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self._s3.head_bucket(Bucket=self._bucket)
        except ClientError:
            try:
                self._s3.create_bucket(Bucket=self._bucket)
            except ClientError as e:
                logger.error(f"Error creating bucket: {e}")

    def _get_key(self, group: str, name: str) -> str:
        return f"{group}/{name}"

    def exists(self, group: str, name: str) -> bool:
        key = self._get_key(group, name)
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def store(self, group: str, name: str, data: bytes) -> bool:
        key = self._get_key(group, name)
        try:
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data
            )
            logger.info(f"store [{key}]")
            return True
        except ClientError as e:
            logger.error(f"store [{key}]: {e}")
            return False

    def load(self, group: str, name: str) -> Optional[bytes]:
        key = self._get_key(group, name)
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            data = response['Body'].read()
            logger.info(f"load [{key}]")
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"load [{key}]: not found")
                return None
            logger.error(f"load [{key}]: {e}")
            return None

    def delete(self, group: str, name: str) -> bool:
        key = self._get_key(group, name)
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
            logger.info(f"delete: [{key}]")
            return True
        except ClientError as e:
            logger.error(f"delete [{key}]: {e}")
            return False
