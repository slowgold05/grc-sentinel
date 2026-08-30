from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ruleset.monitoring.models import TestResult


@dataclass(frozen=True)
class AwsConnection:
    """Read-only AWS service clients, injectable for testing."""

    s3: Any
    cloudtrail: Any
    iam: Any

    @classmethod
    def from_default_session(cls, region_name: str | None = None) -> "AwsConnection":
        session = boto3.Session(region_name=region_name)
        return cls(
            s3=session.client("s3"),
            cloudtrail=session.client("cloudtrail"),
            iam=session.client("iam"),
        )


def _result(status: str, observed: dict[str, object]) -> TestResult:
    return TestResult(status=status, observed=observed, tested_at=datetime.now(UTC))


class AwsS3EncryptionTest:
    test_id = "aws-s3-default-encryption-v1"
    control_ids = ["SC-28"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, AwsConnection):
            raise TypeError("AwsConnection required")
        try:
            buckets = [item["Name"] for item in connection.s3.list_buckets().get("Buckets", [])]
            unencrypted = []
            for bucket in buckets:
                try:
                    connection.s3.get_bucket_encryption(Bucket=bucket)
                except ClientError as exc:
                    if exc.response.get("Error", {}).get("Code") in {
                        "ServerSideEncryptionConfigurationNotFoundError",
                        "404",
                    }:
                        unencrypted.append(bucket)
                    else:
                        raise
            return _result(
                "pass" if not unencrypted else "fail",
                {"buckets_checked": len(buckets), "unencrypted": unencrypted},
            )
        except (BotoCoreError, ClientError, KeyError, TypeError) as exc:
            return _result("error", {"reason": type(exc).__name__})


class AwsCloudTrailTest:
    test_id = "aws-cloudtrail-enabled-v1"
    control_ids = ["AU-2"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, AwsConnection):
            raise TypeError("AwsConnection required")
        try:
            trails = connection.cloudtrail.describe_trails(includeShadowTrails=False).get(
                "trailList", []
            )
            stopped = [
                trail["Name"]
                for trail in trails
                if not connection.cloudtrail.get_trail_status(Name=trail["TrailARN"]).get(
                    "IsLogging", False
                )
            ]
            return _result(
                "pass" if trails and not stopped else "fail",
                {"trails_checked": len(trails), "stopped": stopped},
            )
        except (BotoCoreError, ClientError, KeyError, TypeError) as exc:
            return _result("error", {"reason": type(exc).__name__})


class AwsIamMfaTest:
    test_id = "aws-iam-user-mfa-v1"
    control_ids = ["IA-2"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, AwsConnection):
            raise TypeError("AwsConnection required")
        try:
            users = [
                user["UserName"]
                for page in connection.iam.get_paginator("list_users").paginate()
                for user in page.get("Users", [])
            ]
            without_mfa = [
                user
                for user in users
                if not connection.iam.list_mfa_devices(UserName=user).get("MFADevices", [])
            ]
            return _result(
                "pass" if not without_mfa else "fail",
                {"users_checked": len(users), "without_mfa": without_mfa},
            )
        except (BotoCoreError, ClientError, KeyError, TypeError) as exc:
            return _result("error", {"reason": type(exc).__name__})
