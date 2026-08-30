import json

from ruleset.kb.ingest_oscal import parse_oscal


def test_ac_2_has_thirteen_enhancements_and_parameters() -> None:
    payload = {
        "catalog": {
            "metadata": {"title": "NIST SP 800-53", "version": "5.2.0"},
            "groups": [
                {
                    "controls": [
                        {
                            "id": "ac-2",
                            "title": "Account Management",
                            "params": [{"id": f"ac-02_odp.{number:02}"} for number in range(1, 11)],
                            "parts": [{"name": "statement", "prose": "Manage system accounts."}],
                            "controls": [
                                {"id": f"ac-2.{number}", "title": f"Enhancement {number}"}
                                for number in range(1, 14)
                            ],
                        }
                    ]
                }
            ],
        }
    }

    control = parse_oscal(json.dumps(payload)).catalog.groups[0].controls[0]

    assert control.id == "ac-2"
    assert len(control.controls) == 13
    assert [parameter["id"] for parameter in control.params] == [
        f"ac-02_odp.{number:02}" for number in range(1, 11)
    ]
