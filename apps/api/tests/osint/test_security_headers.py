from ruleset.osint.security_headers import grade_security_headers


def test_grades_header_presence_case_insensitively() -> None:
    posture = grade_security_headers(
        {
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        }
    )
    assert posture.grade == "A"
    assert posture.missing == []
    assert grade_security_headers({}).grade == "F"
