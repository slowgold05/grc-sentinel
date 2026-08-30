import httpx

from ruleset.monitoring.github import (
    GitHubBranchProtectionTest,
    GitHubConnection,
    GitHubOrgMfaTest,
    GitHubSecretScanningTest,
)


def test_github_control_checks_use_read_only_endpoints() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.headers["authorization"] == "Bearer test-token"
        if request.url.path == "/orgs/acme":
            return httpx.Response(200, json={"two_factor_requirement_enabled": True})
        if request.url.path == "/orgs/acme/repos":
            return httpx.Response(
                200,
                json=[
                    {
                        "name": "app",
                        "default_branch": "main",
                        "security_and_analysis": {
                            "secret_scanning": {"status": "enabled"}
                        },
                    }
                ],
            )
        if request.url.path == "/repos/acme/app/branches/main/protection":
            return httpx.Response(200, json={})
        return httpx.Response(404)

    connection = GitHubConnection(
        organization="acme",
        token="test-token",
        transport=httpx.MockTransport(handler),
    )

    assert GitHubOrgMfaTest().run(connection).status == "pass"
    assert GitHubBranchProtectionTest().run(connection).status == "pass"
    assert GitHubSecretScanningTest().run(connection).status == "pass"
