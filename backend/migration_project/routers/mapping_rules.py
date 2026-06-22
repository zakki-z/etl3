from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from migration_project.repositories.mapping_rule_repository import MappingRuleRepository
from migration_project.routers.deps import get_db

router = APIRouter(prefix="/api/v1/mapping-rules", tags=["mapping-rules"])

_repo = MappingRuleRepository()


class MappingRuleIn(BaseModel):
    rule_name: str
    source_field: str | None = None
    target_field: str
    transform_type: str = "direct"
    transform_params: dict | None = None
    is_active: bool = True


@router.get("")
def list_mapping_rules(db: Session = Depends(get_db)) -> list[dict]:
    """Return all mapping rules."""
    rows = db.execute(
        text("""
            SELECT id, rule_name, source_field, target_field,
                   transform_type, transform_params, is_active, created_at
            FROM mapping_rule ORDER BY id
        """)
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{rule_id}")
def get_mapping_rule(rule_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.execute(
        text("""
            SELECT id, rule_name, source_field, target_field,
                   transform_type, transform_params, is_active, created_at
            FROM mapping_rule WHERE id = :id
        """),
        {"id": rule_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Mapping rule not found")
    return dict(row)


@router.post("", status_code=201)
def create_or_update_mapping_rule(body: MappingRuleIn, db: Session = Depends(get_db)) -> dict:
    """Upsert a mapping rule by rule_name."""
    rule_id = _repo.upsert(db, {
        "rule_name": body.rule_name,
        "source_field": body.source_field,
        "target_field": body.target_field,
        "transform_type": body.transform_type,
        "transform_params": body.transform_params,
        "is_active": 1 if body.is_active else 0,
    })
    db.commit()
    return {"id": rule_id, "rule_name": body.rule_name}


@router.patch("/{rule_id}/toggle")
def toggle_mapping_rule(rule_id: int, db: Session = Depends(get_db)) -> dict:
    """Toggle a rule between active and inactive."""
    rule = _repo.get_by_id(db, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Mapping rule not found")
    new_state = not bool(rule.is_active)
    _repo.set_active(db, rule_id, new_state)
    db.commit()
    return {"id": rule_id, "is_active": new_state}
