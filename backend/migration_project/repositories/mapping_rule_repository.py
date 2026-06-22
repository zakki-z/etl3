from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from migration_project.models.mapping_rule import MappingRule


class MappingRuleRepository:
    def get_active(self, session: Session) -> list[MappingRule]:
        """Return all active mapping rules ordered by id."""
        return list(
            session.execute(
                select(MappingRule).where(MappingRule.is_active == 1).order_by(MappingRule.id)
            ).scalars().all()
        )

    def get_by_id(self, session: Session, rule_id: int) -> MappingRule | None:
        return session.get(MappingRule, rule_id)

    def upsert(self, session: Session, data: dict) -> int:
        """Insert or update a single rule. Returns the rule id."""
        stmt = insert(MappingRule).values(**data)
        stmt = stmt.on_duplicate_key_update(
            source_field=stmt.inserted.source_field,
            target_field=stmt.inserted.target_field,
            transform_type=stmt.inserted.transform_type,
            transform_params=stmt.inserted.transform_params,
            is_active=stmt.inserted.is_active,
        )
        session.execute(stmt)
        session.flush()
        row = session.execute(
            select(MappingRule.id).where(MappingRule.rule_name == data["rule_name"])
        ).scalar_one()
        return int(row)

    def set_active(self, session: Session, rule_id: int, is_active: bool) -> bool:
        rule = session.get(MappingRule, rule_id)
        if rule is None:
            return False
        rule.is_active = 1 if is_active else 0
        return True
