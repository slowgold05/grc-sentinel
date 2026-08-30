from uuid import UUID

import httpx
from pydantic import BaseModel
from sqlalchemy import Engine

from ruleset.monitoring.connections import GitHubCredentials, load_connection
from ruleset.monitoring.evidence import append_evidence
from ruleset.monitoring.github import (
    GitHubBranchProtectionTest,
    GitHubConnection,
    GitHubOrgMfaTest,
    GitHubSecretScanningTest,
)
from ruleset.monitoring.models import TestResult


class EvidenceRun(BaseModel):
    evidence_id: UUID
    test_id: str
    result: TestResult


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
    runs = []
    for test in (GitHubOrgMfaTest(), GitHubBranchProtectionTest(), GitHubSecretScanningTest()):
        result = test.run(connection)
        evidence_id = append_evidence(engine, org_id, test, result, result.observed)
        runs.append(EvidenceRun(evidence_id=evidence_id, test_id=test.test_id, result=result))
    return runs
