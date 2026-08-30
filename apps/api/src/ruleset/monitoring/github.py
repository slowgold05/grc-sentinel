from dataclasses import dataclass
from datetime import UTC, datetime
import re
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict

from ruleset.monitoring.models import TestResult

_SLUG = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


@dataclass(frozen=True)
class GitHubConnection:
    organization: str
    token: str
    transport: httpx.BaseTransport | None = None

    def __post_init__(self) -> None:
        if not _SLUG.fullmatch(self.organization) or not self.token:
            raise ValueError("GitHub organization and token are required")


class _Organization(BaseModel):
    model_config = ConfigDict(extra="ignore")
    two_factor_requirement_enabled: bool


class _SecurityFeature(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: str


class _SecurityAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    secret_scanning: _SecurityFeature | None = None


class _Repository(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    default_branch: str
    archived: bool = False
    security_and_analysis: _SecurityAnalysis | None = None


def _client(connection: GitHubConnection) -> httpx.Client:
    return httpx.Client(
        base_url="https://api.github.com",
        headers={
            "Authorization": f"Bearer {connection.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        transport=connection.transport,
        timeout=20,
    )


def _result(status: str, observed: dict[str, object]) -> TestResult:
    return TestResult(status=status, observed=observed, tested_at=datetime.now(UTC))


def _repositories(client: httpx.Client, organization: str) -> list[_Repository]:
    # ponytail: first 100 repositories; add Link-header pagination for larger organizations.
    response = client.get(f"/orgs/{organization}/repos", params={"per_page": 100, "type": "all"})
    response.raise_for_status()
    return [_Repository.model_validate(repo) for repo in response.json()]


class GitHubOrgMfaTest:
    test_id = "github-org-mfa-v1"
    control_ids = ["IA-2", "CC6.1"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, GitHubConnection):
            raise TypeError("GitHubConnection required")
        try:
            with _client(connection) as client:
                response = client.get(f"/orgs/{connection.organization}")
                response.raise_for_status()
                enabled = _Organization.model_validate(
                    response.json()
                ).two_factor_requirement_enabled
            return _result("pass" if enabled else "fail", {"enabled": enabled})
        except (httpx.HTTPError, ValueError) as exc:
            return _result("error", {"reason": type(exc).__name__})


class GitHubBranchProtectionTest:
    test_id = "github-default-branch-protection-v1"
    control_ids = ["CM-3", "SA-11"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, GitHubConnection):
            raise TypeError("GitHubConnection required")
        try:
            with _client(connection) as client:
                repositories = [repo for repo in _repositories(client, connection.organization) if not repo.archived]
                unprotected = []
                for repo in repositories:
                    response = client.get(
                        f"/repos/{connection.organization}/{quote(repo.name, safe='')}/branches/"
                        f"{quote(repo.default_branch, safe='')}/protection"
                    )
                    if response.status_code == 404:
                        unprotected.append(repo.name)
                    else:
                        response.raise_for_status()
            return _result(
                "pass" if not unprotected else "fail",
                {"repositories_checked": len(repositories), "unprotected": unprotected},
            )
        except (httpx.HTTPError, ValueError) as exc:
            return _result("error", {"reason": type(exc).__name__})


class GitHubSecretScanningTest:
    test_id = "github-secret-scanning-v1"
    control_ids = ["SA-11", "RA-5"]

    def run(self, connection: object) -> TestResult:
        if not isinstance(connection, GitHubConnection):
            raise TypeError("GitHubConnection required")
        try:
            with _client(connection) as client:
                repositories = [repo for repo in _repositories(client, connection.organization) if not repo.archived]
            unavailable = [
                repo.name
                for repo in repositories
                if repo.security_and_analysis is None or repo.security_and_analysis.secret_scanning is None
            ]
            disabled = [
                repo.name
                for repo in repositories
                if repo.security_and_analysis is not None
                and repo.security_and_analysis.secret_scanning is not None
                and repo.security_and_analysis.secret_scanning.status != "enabled"
            ]
            if unavailable:
                return _result("error", {"unavailable": unavailable})
            return _result(
                "pass" if not disabled else "fail",
                {"repositories_checked": len(repositories), "disabled": disabled},
            )
        except (httpx.HTTPError, ValueError) as exc:
            return _result("error", {"reason": type(exc).__name__})
