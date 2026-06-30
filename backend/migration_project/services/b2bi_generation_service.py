from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from migration_project.models.b2bi_inbound_flow import B2biInboundFlow
from migration_project.models.b2bi_partner import B2biPartner, MigrationStatus
from migration_project.models.b2bi_partner_delivery import B2biPartnerDelivery
from migration_project.models.community import Community
from migration_project.models.flow import CftFlow
from migration_project.models.moncft_config import MonCftConfig
from migration_project.models.partner import CftPartner
from migration_project.models.tcp import CftTcp
from migration_project.models.transfer import Transfer

# Row statuses that generation is allowed to overwrite. Once a row has been
# pushed/validated/migrated by hand (or by a later phase), re-running
# generation must not clobber that progress — it only refreshes rows still
# sitting in DRAFT or ERROR.
_OVERWRITABLE_STATUSES = {MigrationStatus.DRAFT, MigrationStatus.ERROR}


def _truncate(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    return value[:max_len]


@dataclass
class GenerationReport:
    community_id: str
    partners_processed: int = 0
    partners_ready: int = 0
    partners_draft: int = 0
    partners_error: int = 0
    deliveries_created: int = 0
    deliveries_updated: int = 0
    inbound_flows_created: int = 0
    inbound_flows_updated: int = 0
    skipped_rows: int = 0
    errors: list[str] = field(default_factory=list)


class B2biGenerationService:
    """Generates B2Bi Trading Partner config rows directly from the CFT
    inventory tables (cft_partner, cft_tcp, cft_flow, transfer, moncft_config),
    writing results straight into the live per-row migration_status schema:
    b2bi_partner, b2bi_partner_delivery, b2bi_inbound_flow.

    There is no intermediate mapping_rule/generation_job/exception_log/
    b2bi_config layer (retired). Field mapping is intentionally explicit and
    documented inline below rather than data-driven, since the only mapping
    rules that existed previously covered a handful of trivial fields.
    """

    def generate(
        self,
        session: Session,
        community_id: str,
        partner_ids: list[str] | None = None,
    ) -> GenerationReport:
        community = session.get(Community, community_id)
        if community is None:
            raise ValueError(f"Community '{community_id}' does not exist")

        report = GenerationReport(community_id=community_id)

        partner_query = select(CftPartner)
        if partner_ids:
            partner_query = partner_query.where(CftPartner.id.in_(partner_ids))
        cft_partners = session.execute(partner_query).scalars().all()

        for cft_partner in cft_partners:
            try:
                self._generate_for_partner(session, cft_partner, community_id, report)
            except Exception as exc:  # noqa: BLE001 — one bad partner must not abort the run
                report.errors.append(f"{cft_partner.id}: {exc}")
                report.partners_error += 1
            report.partners_processed += 1

        session.flush()
        return report

    # ── Per-partner generation ──────────────────────────────────────────

    def _generate_for_partner(
        self,
        session: Session,
        cft_partner: CftPartner,
        community_id: str,
        report: GenerationReport,
    ) -> None:
        tcp = session.get(CftTcp, cft_partner.id)
        transfers = session.execute(
            select(Transfer).where(Transfer.partner_id == cft_partner.id)
        ).scalars().all()

        b2bi_partner = self._upsert_partner(session, cft_partner, community_id)

        has_blocking_error = False
        for transfer in transfers:
            cft_flow = session.get(CftFlow, transfer.idf_id)
            if cft_flow is None:
                report.skipped_rows += 1
                continue

            moncft = session.execute(
                select(MonCftConfig).where(MonCftConfig.transfer_id == transfer.id)
            ).scalars().first()

            if cft_flow.direct == "send":
                if tcp is None or not tcp.host:
                    # A send (outbound delivery) channel needs a network
                    # target. Without cft_tcp.host there's nothing to build.
                    has_blocking_error = True
                    report.skipped_rows += 1
                    continue
                created = self._upsert_delivery(session, b2bi_partner, transfer, cft_flow, tcp, moncft)
                if created:
                    report.deliveries_created += 1
                else:
                    report.deliveries_updated += 1
            elif cft_flow.direct == "recv":
                created = self._upsert_inbound_flow(session, b2bi_partner, transfer, cft_flow, moncft)
                if created:
                    report.inbound_flows_created += 1
                else:
                    report.inbound_flows_updated += 1
            else:
                report.skipped_rows += 1

        # Only move the partner's own status if it's still ours to advance.
        if b2bi_partner.migration_status in _OVERWRITABLE_STATUSES:
            if has_blocking_error:
                b2bi_partner.migration_status = MigrationStatus.ERROR
                report.partners_error += 1
            elif transfers:
                b2bi_partner.migration_status = MigrationStatus.READY
                report.partners_ready += 1
            else:
                b2bi_partner.migration_status = MigrationStatus.DRAFT
                report.partners_draft += 1
        elif b2bi_partner.migration_status == MigrationStatus.READY:
            report.partners_ready += 1

    # ── Row builders ─────────────────────────────────────────────────────

    def _upsert_partner(
        self, session: Session, cft_partner: CftPartner, community_id: str
    ) -> B2biPartner:
        existing = session.execute(
            select(B2biPartner).where(B2biPartner.partner_code == cft_partner.id)
        ).scalars().first()

        party_name = cft_partner.nrpart or cft_partner.nspart or cft_partner.id

        if existing is None:
            partner = B2biPartner(
                partner_code=cft_partner.id,
                party_name=party_name,
                partner_contact=cft_partner.partner_contact,
                nrpart=cft_partner.nrpart,
                ssl=cft_partner.ssl,
                nspart=_truncate(cft_partner.nspart, 19),
                community_id=community_id,
                migration_status=MigrationStatus.DRAFT,
            )
            session.add(partner)
            session.flush()  # assign b2bi_partner_id
            return partner

        if existing.migration_status in _OVERWRITABLE_STATUSES:
            existing.party_name = party_name
            existing.partner_contact = cft_partner.partner_contact
            existing.nrpart = cft_partner.nrpart
            existing.ssl = cft_partner.ssl
            existing.nspart = _truncate(cft_partner.nspart, 19)
            existing.community_id = community_id
        return existing

    def _upsert_delivery(
        self,
        session: Session,
        b2bi_partner: B2biPartner,
        transfer: Transfer,
        cft_flow: CftFlow,
        tcp: CftTcp,
        moncft: MonCftConfig | None,
    ) -> bool:
        """Returns True if a new row was created, False if an existing row
        was updated (or left untouched because it had already progressed)."""
        existing = session.execute(
            select(B2biPartnerDelivery).where(B2biPartnerDelivery.transfer_id == transfer.id)
        ).scalars().first()

        values = dict(
            friendly_name=f"{cft_flow.idf_code}-{transfer.partner_id}",
            b2bi_delivery_remote_id=None,
            host=tcp.host,
            port=tcp.cnxout,
            parm=moncft.parm if moncft else None,
            idf=cft_flow.idf_code,
            nfname=moncft.nfname if moncft else None,
            # CFT's xlate flag marks records needing EBCDIC<->ASCII
            # translation; used here as a best-effort proxy for encoding.
            data_encoding="EBCDIC" if cft_flow.xlate else "ASCII",
            record_format=cft_flow.frecfm,
            record_length=cft_flow.flrecl,
            fname=moncft.fname if moncft and moncft.fname else cft_flow.fname,
            b2bi_partner_id=b2bi_partner.b2bi_partner_id,
        )

        if existing is None:
            delivery = B2biPartnerDelivery(
                transfer_id=transfer.id,
                migration_status=MigrationStatus.DRAFT,
                **values,
            )
            session.add(delivery)
            return True

        if existing.migration_status in _OVERWRITABLE_STATUSES:
            for key, value in values.items():
                setattr(existing, key, value)
        return False

    def _upsert_inbound_flow(
        self,
        session: Session,
        b2bi_partner: B2biPartner,
        transfer: Transfer,
        cft_flow: CftFlow,
        moncft: MonCftConfig | None,
    ) -> bool:
        existing = session.execute(
            select(B2biInboundFlow).where(B2biInboundFlow.transfer_id == transfer.id)
        ).scalars().first()

        fname = moncft.fname if moncft and moncft.fname else cft_flow.fname
        nfname = moncft.nfname if moncft else None
        values = dict(
            idf=cft_flow.idf_code,
            fname=fname,
            parm=moncft.parm if moncft else None,
            nfname=nfname,
            # No dedicated CFT field for a rename rule; when the inbound and
            # post-rename filenames differ, that difference *is* the rule.
            rename_rule=nfname if (nfname and nfname != fname) else None,
            b2bi_partner_id=b2bi_partner.b2bi_partner_id,
        )

        if existing is None:
            inbound_flow = B2biInboundFlow(
                transfer_id=transfer.id,
                migration_status=MigrationStatus.DRAFT,
                **values,
            )
            session.add(inbound_flow)
            return True

        if existing.migration_status in _OVERWRITABLE_STATUSES:
            for key, value in values.items():
                setattr(existing, key, value)
        return False