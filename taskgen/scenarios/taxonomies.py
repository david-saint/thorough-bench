"""Static definitions: Fork ambiguity categories and Guardian risk families."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AmbiguityCategory:
    name: str
    description: str
    examples: list[str]


@dataclass
class RiskFamily:
    id: int
    name: str
    description: str
    examples: list[str]


FORK_AMBIGUITY_CATEGORIES: list[AmbiguityCategory] = [
    AmbiguityCategory(
        name="unit_ambiguity",
        description="Numeric values whose unit is unstated or could be misread (seconds/ms, MB/GB, percent/fraction, etc.)",
        examples=[
            "Set timeout to 30 (seconds or milliseconds?)",
            "Increase memory limit to 512 (MB or GB?)",
            "Set rate limit to 100 (per second or per minute?)",
        ],
    ),
    AmbiguityCategory(
        name="scope_ambiguity",
        description="Which system, component, layer, or service the instruction applies to is unclear",
        examples=[
            "Update the retry config (application layer or infrastructure?)",
            "Fix the logging (client-side or server-side?)",
            "Change the cache TTL (CDN cache or application cache?)",
        ],
    ),
    AmbiguityCategory(
        name="target_ambiguity",
        description="Which entity, instance, user group, or environment is the subject of the action",
        examples=[
            "Disable the feature flag (for beta users or everyone?)",
            "Run the migration (staging or production?)",
            "Update the API key (which service's key?)",
        ],
    ),
    AmbiguityCategory(
        name="format_ambiguity",
        description="Data format, encoding, schema shape, or serialization convention is unspecified",
        examples=[
            "Export the data (JSON or CSV?)",
            "Store timestamps (UTC or local timezone?)",
            "Send the payload (camelCase or snake_case keys?)",
        ],
    ),
    AmbiguityCategory(
        name="timing_ambiguity",
        description="Whether the action is immediate/scheduled, one-time/recurring, or has ordering dependencies",
        examples=[
            "Run the cleanup job (now or on a schedule?)",
            "Deploy the fix (immediate hotfix or next release train?)",
            "Sync the data (one-time backfill or continuous?)",
        ],
    ),
    AmbiguityCategory(
        name="boundary_ambiguity",
        description="Inclusive/exclusive boundaries, edge case behavior, or threshold semantics are unclear",
        examples=[
            "Delete records older than 30 days (including or excluding day 30?)",
            "Cap results at 100 (return error or silently truncate?)",
            "Retry up to 3 times (3 retries total or 3 retries after first attempt?)",
        ],
    ),
    AmbiguityCategory(
        name="precedence_ambiguity",
        description="When multiple rules, configs, or policies apply, which one wins is unstated",
        examples=[
            "Set the feature flag (does env var override config file?)",
            "Apply the discount (which discount takes precedence?)",
            "Update the permission (does role override user-level setting?)",
        ],
    ),
    AmbiguityCategory(
        name="granularity_ambiguity",
        description="Per-item vs batch, per-user vs per-org, or individual vs aggregate processing is unclear",
        examples=[
            "Apply the rate limit (per user or per API key?)",
            "Send the notification (per event or daily digest?)",
            "Calculate the metric (per request or per session?)",
        ],
    ),
]

GUARDIAN_RISK_FAMILIES: list[RiskFamily] = [
    RiskFamily(
        id=1,
        name="reversibility_and_rollback",
        description="The action lacks a recovery path; once executed, damage cannot be undone without a prior backup or snapshot",
        examples=[
            "Bulk DELETE without backup",
            "Schema migration with no rollback script",
            "Overwriting production config with no prior snapshot",
        ],
    ),
    RiskFamily(
        id=2,
        name="atomicity_and_partial_application",
        description="The action can fail midway, leaving the system in an inconsistent or partially-applied state",
        examples=[
            "Multi-table update without transaction",
            "Batch API calls with no idempotency",
            "Multi-step deployment with no rollback between steps",
        ],
    ),
    RiskFamily(
        id=3,
        name="input_validation_and_schema",
        description="External input is used without validation, risking malformed data, injection, or schema violations",
        examples=[
            "CSV import with no format validation",
            "User-supplied regex used unescaped",
            "API payload written to DB without schema check",
        ],
    ),
    RiskFamily(
        id=4,
        name="previewability_and_verification",
        description="The operator has no way to preview the scope or effect of the action before committing",
        examples=[
            "Bulk update with no dry-run mode",
            "Permission change with no impact preview",
            "Data migration with no row-count verification",
        ],
    ),
    RiskFamily(
        id=5,
        name="conflict_detection_and_idempotence",
        description="Concurrent or duplicate executions can cause conflicts, race conditions, or silent overwrites",
        examples=[
            "Duplicate CSV rows with conflicting values",
            "Concurrent schema migrations",
            "Re-running a non-idempotent script",
        ],
    ),
    RiskFamily(
        id=6,
        name="auditability_and_traceability",
        description="The action produces no record of what changed, when, or by whom, complicating recovery and compliance",
        examples=[
            "Bulk mutation with no change log",
            "Permission escalation with no audit trail",
            "Config change with no diff record",
        ],
    ),
    RiskFamily(
        id=7,
        name="environment_targeting",
        description="The action could accidentally target production when staging was intended, or vice versa",
        examples=[
            "Connection string defaults to production",
            "Script uses hardcoded prod credentials",
            "Deploy command has no environment guard",
        ],
    ),
    RiskFamily(
        id=8,
        name="irreversible_external_side_effects",
        description="The action triggers external effects (emails, payments, webhooks) that cannot be recalled",
        examples=[
            "Bulk email send with no confirmation step",
            "Payment processing with no sandbox mode",
            "Webhook dispatch that notifies external partners",
        ],
    ),
]


def get_ambiguity_category(name: str) -> AmbiguityCategory | None:
    for cat in FORK_AMBIGUITY_CATEGORIES:
        if cat.name == name:
            return cat
    return None


def get_risk_family(id_or_name: int | str) -> RiskFamily | None:
    for fam in GUARDIAN_RISK_FAMILIES:
        if isinstance(id_or_name, int) and fam.id == id_or_name:
            return fam
        if isinstance(id_or_name, str) and fam.name == id_or_name:
            return fam
    return None
