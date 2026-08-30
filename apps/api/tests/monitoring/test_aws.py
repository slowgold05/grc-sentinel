from ruleset.monitoring.aws import (
    AwsCloudTrailTest,
    AwsConnection,
    AwsIamMfaTest,
    AwsS3EncryptionTest,
)


class S3:
    def list_buckets(self) -> dict:
        return {"Buckets": [{"Name": "evidence"}]}

    def get_bucket_encryption(self, **kwargs: str) -> dict:
        return {"ServerSideEncryptionConfiguration": {}}


class CloudTrail:
    def describe_trails(self, **kwargs: bool) -> dict:
        return {"trailList": [{"Name": "audit", "TrailARN": "arn:trail"}]}

    def get_trail_status(self, **kwargs: str) -> dict:
        return {"IsLogging": True}


class Paginator:
    def paginate(self) -> list[dict]:
        return [{"Users": [{"UserName": "operator"}]}]


class Iam:
    def get_paginator(self, name: str) -> Paginator:
        assert name == "list_users"
        return Paginator()

    def list_mfa_devices(self, **kwargs: str) -> dict:
        return {"MFADevices": [{"SerialNumber": "arn:mfa"}]}


def test_aws_control_checks_pass_for_compliant_observations() -> None:
    connection = AwsConnection(s3=S3(), cloudtrail=CloudTrail(), iam=Iam())

    assert AwsS3EncryptionTest().run(connection).status == "pass"
    assert AwsCloudTrailTest().run(connection).status == "pass"
    assert AwsIamMfaTest().run(connection).status == "pass"
