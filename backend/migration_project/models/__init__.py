from migration_project.models.b2bi_inbound_flow import B2biInboundFlow
from migration_project.models.b2bi_partner import B2biPartner, MigrationStatus
from migration_project.models.b2bi_partner_delivery import B2biPartnerDelivery
from migration_project.models.boscosend_config import BoscoSendConfig
from migration_project.models.community import Community
from migration_project.models.community_routing_id import CommunityRoutingId
from migration_project.models.flow import CftFlow
from migration_project.models.flow_action import ActionScope, FlowAction
from migration_project.models.moncft_config import MonCftConfig
from migration_project.models.partner import CftPartner
from migration_project.models.post_processing_script import PostProcessingScript
from migration_project.models.server import Server
from migration_project.models.tcp import CftTcp
from migration_project.models.transfer import Transfer

# ── Read-only VIEW mappings ────────────────────────────────────────────
# Mapped against ViewBase, NOT Base — excluded from Base.metadata.create_all()
# on purpose. See view_base.py.
from migration_project.models.cft_flow_xlate_view import CftFlowXlateEnabled
from migration_project.models.cft_partner_ssl_view import CftPartnerSslEnabled
from migration_project.models.view_base import ViewBase

__all__ = [
    "ActionScope",
    "B2biInboundFlow",
    "B2biPartner",
    "B2biPartnerDelivery",
    "BoscoSendConfig",
    "CftFlow",
    "CftFlowXlateEnabled",
    "CftPartner",
    "CftPartnerSslEnabled",
    "CftTcp",
    "Community",
    "CommunityRoutingId",
    "FlowAction",
    "MigrationStatus",
    "MonCftConfig",
    "PostProcessingScript",
    "Server",
    "Transfer",
    "ViewBase",
]