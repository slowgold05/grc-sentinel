from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import Engine

from ruleset.monitoring.aws import (
    AwsCloudTrailTest,
    AwsConnection,
    AwsIamMfaTest,
    AwsS3EncryptionTest,
)
from ruleset.monitoring.connections import AwsCredentials, GitHubCredentials, load_connection
from ruleset.monitoring.evidence import append_evidence
from ruleset.monitoring.github import (
    GitHubBranchProtectionTest,
    GitHubConnection,
    GitHubOrgMfaTest,
    GitHubSecretScanningTest,
)
from ruleset.monitoring.models import ControlTest, TestResult


class EvidenceRun(BaseModel):
    evidence_id: UUID
    test_id: str
    drift: bool
    result: TestResult


def _run_checks(
    engine: Engine, org_id: UUID, connection: object, tests: tuple[ControlTest, ...]
) -> list[EvidenceRun]:
    runs = []
    for test in tests:
        result = test.run(connection)
        write = append_evidence(engine, org_id, test, result, result.observed)
        runs.append(
            EvidenceRun(
                evidence_id=write.id, test_id=test.test_id, drift=write.drift, result=result
            )
        )
    return runs


def run_github_checks(
    engine: Engine,
    org_id: UUID,
    master_key: bytes,
    transport: httpx.BaseTransport | None = None,
) -> list[EvidenceRun]:
    """Run every read-only GitHub test and append its immutable evidence."""
    stored = load_connection(engine, org_id, "github", master_key)
    if not isinstance(stored, GitHubCredentials):
        raise LookupError("GitHub connection not found")
    connection = GitHubConnection(
        stored.organization, stored.token.get_secret_value(), transport
    )
    return _run_checks(
        engine,
        org_id,
        connection,
        (GitHubOrgMfaTest(), GitHubBranchProtectionTest(), GitHubSecretScanningTest()),
    )


def run_aws_checks(engine: Engine, org_id: UUID, master_key: bytes) -> list[EvidenceRun]:
    """Assume a read-only AWS role, run every check, and append evidence."""
    stored = load_connection(engine, org_id, "aws", master_key)
    if not isinstance(stored, AwsCredentials):
        raise LookupError("AWS connection not found")
    connection = AwsConnection.from_assumed_role(
        stored.role_arn, stored.external_id.get_secret_value(), stored.region
    )
    return _run_checks(
        engine,
        org_id,
        connection,
        (AwsS3EncryptionTest(), AwsCloudTrailTest(), AwsIamMfaTest()),
    )
