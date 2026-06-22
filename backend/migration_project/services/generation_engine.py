from __future__ import annotations

from dataclasses import dataclass, field

from migration_project.models.mapping_rule import MappingRule
from migration_project.services.context_builder import PartnerContext


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class GenerationException:
    severity: str          # 'BLOCKING' | 'WARNING'
    exception_type: str
    message: str


@dataclass
class GenerationResult:
    partner_id: str
    payload: dict
    exceptions: list[GenerationException] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return any(e.severity == "BLOCKING" for e in self.exceptions)


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

def _apply_rule(rule: MappingRule, ctx: PartnerContext) -> tuple[str, object | None]:
    """Apply a single mapping rule to the context. Returns (target_field, value)."""
    params = rule.transform_params or {}

    if rule.transform_type == "static":
        return rule.target_field, params.get("value")

    if rule.source_field is None:
        return rule.target_field, None

    # Resolve dot-path on ctx (e.g. "partner.ssl" -> ctx.ssl)
    parts = rule.source_field.split(".", 1)
    raw_value: object | None = None
    if len(parts) == 2:
        _, attr = parts
        raw_value = getattr(ctx, attr, None)

    if rule.transform_type == "direct":
        return rule.target_field, raw_value

    if rule.transform_type == "lookup":
        mapping: dict = params  # e.g. {"send": "SENDER", "recv": "RECEIVER"}
        return rule.target_field, mapping.get(str(raw_value), raw_value)

    if rule.transform_type == "template":
        template: str = params.get("template", "")
        value = template.format(value=raw_value, ctx=ctx)
        return rule.target_field, value

    return rule.target_field, raw_value


def _set_nested(payload: dict, dot_path: str, value: object) -> None:
    """Write value into nested dict using a dot-path key."""
    keys = dot_path.split(".")
    current = payload
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value


# ---------------------------------------------------------------------------
# Validation checks (pure functions, easy to extend)
# ---------------------------------------------------------------------------

def _check_host(ctx: PartnerContext) -> GenerationException | None:
    if not ctx.host:
        return GenerationException(
            severity="BLOCKING",
            exception_type="MISSING_HOST",
            message=f"Partner '{ctx.partner_id}' has no TCP host configured.",
        )
    return None


def _check_ssl_consistency(ctx: PartnerContext) -> GenerationException | None:
    """SSL flag present but no SAP (Application Service Point) configured."""
    if ctx.ssl and not ctx.sap:
        return GenerationException(
            severity="WARNING",
            exception_type="SSL_WITHOUT_SAP",
            message=f"Partner '{ctx.partner_id}' has SSL enabled but no SAP configured.",
        )
    return None


def _check_bucket_c(ctx: PartnerContext) -> GenerationException | None:
    if ctx.has_bucket_c_script:
        return GenerationException(
            severity="BLOCKING",
            exception_type="SCRIPT_BUCKET_C",
            message=(
                f"Partner '{ctx.partner_id}' has at least one Bucket C post-processing script "
                f"that cannot be automatically migrated and requires manual review."
            ),
        )
    return None


def _check_no_flows(ctx: PartnerContext) -> GenerationException | None:
    if not ctx.flows:
        return GenerationException(
            severity="WARNING",
            exception_type="NO_FLOWS",
            message=f"Partner '{ctx.partner_id}' has no associated CFT flows.",
        )
    return None


_VALIDATORS = [_check_host, _check_ssl_consistency, _check_bucket_c, _check_no_flows]


# ---------------------------------------------------------------------------
# Engine entry point
# ---------------------------------------------------------------------------

def generate(ctx: PartnerContext, rules: list[MappingRule]) -> GenerationResult:
    """
    Pure function. No database access.
    Takes a PartnerContext and a list of active MappingRules.
    Returns a GenerationResult with the B2Bi payload and any exceptions.
    """
    exceptions: list[GenerationException] = []

    # Run all validation checks first
    for validator in _VALIDATORS:
        exc = validator(ctx)
        if exc is not None:
            exceptions.append(exc)

    # Build the base payload structure
    payload: dict = {
        "trading_partner": {
            "partner_id": ctx.partner_id,
        },
        "network": {},
        "flows": [],
    }

    # Apply mapping rules to populate the payload
    for rule in rules:
        target, value = _apply_rule(rule, ctx)
        if value is not None:
            _set_nested(payload, target, value)

    # Add flows sub-list
    for flow in ctx.flows:
        payload["flows"].append({
            "idf_code": flow.idf_code,
            "direction": "SENDER" if flow.direct == "send" else "RECEIVER",
            "fcode": flow.fcode,
            "ftype": flow.ftype,
            "fname": flow.fname,
            "xlate": bool(flow.xlate),
        })

    return GenerationResult(
        partner_id=ctx.partner_id,
        payload=payload,
        exceptions=exceptions,
    )
