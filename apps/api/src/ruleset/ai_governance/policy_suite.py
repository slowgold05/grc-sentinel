from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Engine, text

from ruleset.generation.context import PolicySectionPlan
from ruleset.generation.faithfulness import (
    FaithfulnessVerdict,
    build_faithfulness_prompt,
    parse_faithfulness_verdict,
)
from ruleset.generation.models import GenerationOutput, RetrievedControl
from ruleset.generation.openai_compatible_client import ModelResult
from ruleset.generation.prompt import build_generation_prompt, parse_generation_output
from ruleset.generation.store import record_model_usage, store_policy
from ruleset.generation.verify import verify_control_citations


class AIPolicyType(StrEnum):
    GOVERNANCE = "ai_governance_accountability"
    ACCEPTABLE_USE = "ai_acceptable_use"
    INVENTORY = "ai_inventory_lifecycle"
    RISK = "ai_risk_impact_assessment"
    DATA = "ai_data_privacy"
    VALIDATION = "ai_model_validation_monitoring"
    THIRD_PARTY = "ai_third_party_foundation_models"
    OVERSIGHT = "ai_human_oversight_transparency_contestability"
    SECURITY = "ai_security_incidents"
    GENERATIVE = "ai_generative_agentic_use"


_POLICY_TITLES = {
    AIPolicyType.GOVERNANCE: "AI Governance and Accountability",
    AIPolicyType.ACCEPTABLE_USE: "AI Acceptable Use",
    AIPolicyType.INVENTORY: "AI Inventory and Lifecycle",
    AIPolicyType.RISK: "AI Risk and Impact Assessment",
    AIPolicyType.DATA: "AI Data and Privacy",
    AIPolicyType.VALIDATION: "AI Model Validation and Monitoring",
    AIPolicyType.THIRD_PARTY: "Third-Party and Foundation Models",
    AIPolicyType.OVERSIGHT: "Human Oversight, Transparency, and Contestability",
    AIPolicyType.SECURITY: "AI Security and Incidents",
    AIPolicyType.GENERATIVE: "Generative and Agentic AI Use",
}

_OBJECTIVE_CORPORA = {
    "nist_ai_rmf": ("NIST AI RMF", "1.0", "voluntary framework"),
    "iso_42001": ("ISO/IEC 42001", "2023", "licensed certifiable standard"),
    "singapore_model_ai_governance": (
        "Singapore Model AI Governance Framework",
        "2nd edition (2020)",
        "voluntary guidance",
    ),
}


class PolicySource(BaseModel):
    framework: str
    version: str
    classification: str
    publisher: str
    source_url: str


class AIPolicyContext(BaseModel):
    engagement_id: UUID
    policy_type: AIPolicyType
    title: str
    plan: PolicySectionPlan
    controls: list[RetrievedControl]
    sources: list[PolicySource]
    gaps: list[str] = Field(default_factory=list)
    company_facts: dict[str, Any]


class AIPolicyDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_ids: list[str] = Field(min_length=1, max_length=50)


class AIPolicyDraftCreated(BaseModel):
    id: UUID
    status: str = "draft"
    sources: list[PolicySource]
    gaps: list[str]


def prepare_ai_policy_context(
    engine: Engine,
    org_id: UUID,
    system_id: UUID,
    policy_type: AIPolicyType,
    control_ids: list[str],
) -> AIPolicyContext:
    """Retrieve only user-selected controls from this system's selected objectives."""
    requested = set(control_ids)
    if not requested:
        raise ValueError("at least one control must be selected")
    with engine.begin() as connection:
        connection.execute(text("SELECT set_config('app.org_id', :id, true)"), {"id": str(org_id)})
        system = connection.execute(
            text(
                "SELECT engagement_id, name, business_purpose, profile FROM ai_systems WHERE id = :id"
            ),
            {"id": system_id},
        ).mappings().one_or_none()
        if system is None:
            raise LookupError("AI system not found")
        objectives = connection.execute(
            text(
                "SELECT framework FROM ai_assurance_objectives "
                "WHERE ai_system_id = :id ORDER BY framework"
            ),
            {"id": system_id},
        ).scalars()

        controls: dict[str, RetrievedControl] = {}
        sources: list[PolicySource] = []
        gaps: list[str] = []
        for objective in objectives:
            name, version, classification = _OBJECTIVE_CORPORA[objective]
            framework = connection.execute(
                text(
                    "SELECT id, publisher, machine_readable_source FROM frameworks "
                    "WHERE name = :name AND version = :version"
                ),
                {"name": name, "version": version},
            ).mappings().one_or_none()
            if framework is None:
                gaps.append(f"{name} {version}: approved control corpus not installed")
                continue
            sources.append(
                PolicySource(
                    framework=name,
                    version=version,
                    classification=classification,
                    publisher=framework["publisher"],
                    source_url=framework["machine_readable_source"],
                )
            )
            rows = connection.execute(
                text(
                    "SELECT control_code, title || E'\\n' || description AS body, params "
                    "FROM controls WHERE framework_id = :id AND valid_to IS NULL "
                    "AND control_code = ANY(:codes) ORDER BY control_code"
                ),
                {"id": framework["id"], "codes": list(requested)},
            ).mappings()
            for row in rows:
                if row["control_code"] in controls:
                    raise ValueError(f"ambiguous control identifier: {row['control_code']}")
                controls[row["control_code"]] = RetrievedControl(
                    control_id=row["control_code"],
                    text=row["body"],
                    parameters={
                        **row["params"],
                        "source_framework": name,
                        "source_version": version,
                        "source_classification": classification,
                    },
                )

    missing = sorted(requested - controls.keys())
    if missing:
        raise ValueError(f"controls are not in a selected installed objective: {', '.join(missing)}")
    title = _POLICY_TITLES[policy_type]
    return AIPolicyContext(
        engagement_id=system["engagement_id"],
        policy_type=policy_type,
        title=title,
        plan=PolicySectionPlan(
            section=title,
            template_body=(
                "Create a draft policy section for the named topic. Preserve source "
                "classification and leave unsupported organization-specific details as gaps."
            ),
            control_ids=[],
        ),
        controls=list(controls.values()),
        sources=sources,
        gaps=gaps,
        company_facts={
            "ai_system_name": system["name"],
            "business_purpose": system["business_purpose"],
            "profile": system["profile"],
        },
    )


async def generate_ai_policy(
    engine: Engine,
    org_id: UUID,
    system_id: UUID,
    policy_type: AIPolicyType,
    request: AIPolicyDraftRequest,
    generate: Callable[[str, dict[str, Any]], Awaitable[ModelResult]],
    verify: Callable[[str, dict[str, Any]], Awaitable[ModelResult]],
) -> AIPolicyDraftCreated:
    """Generate, deterministically cite-check, semantically verify, and store one draft."""
    context = prepare_ai_policy_context(
        engine, org_id, system_id, policy_type, request.control_ids
    )
    generated = await generate(
        build_generation_prompt(context.plan, context.controls, context.company_facts),
        GenerationOutput.model_json_schema(),
    )
    output = parse_generation_output(generated.text)
    citations = verify_control_citations(output, context.controls)
    if not citations.accepted:
        raise ValueError("generated policy contains unsupported control citations")
    verdicts: list[FaithfulnessVerdict] = []
    verifier_usage = [0, 0]
    for statement in output.statements:
        result = await verify(
            build_faithfulness_prompt(statement, context.controls),
            FaithfulnessVerdict.model_json_schema(),
        )
        verifier_usage[0] += result.input_tokens
        verifier_usage[1] += result.output_tokens
        verdicts.append(parse_faithfulness_verdict(result.text))
    if any(not verdict.faithful for verdict in verdicts):
        raise ValueError("generated policy failed faithfulness verification")
    sources = [source.model_dump(mode="json") for source in context.sources]
    policy_id = store_policy(
        engine,
        org_id,
        context.engagement_id,
        policy_type.value,
        context.plan.section,
        output,
        citations,
        verdicts,
        ai_system_id=system_id,
        source_versions=sources,
        gaps=context.gaps,
    )
    record_model_usage(
        engine,
        org_id,
        context.engagement_id,
        provider="openai-compatible",
        model="configured-generation-and-verifier",
        input_tokens=generated.input_tokens + verifier_usage[0],
        output_tokens=generated.output_tokens + verifier_usage[1],
        cost_microusd=0,
    )
    return AIPolicyDraftCreated(id=policy_id, sources=context.sources, gaps=context.gaps)
