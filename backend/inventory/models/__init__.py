from commons.base import metadata

from .server import server_table
from .cfttcp import cfttcp_table
from .cftprot import cftprot_table
from .cftssl import cftssl_table
from .partner import partner_table
from .flow import flow_table
from .processing import processing_table
from .bosco_route import bosco_route_table
from .copilot_activity import copilot_activity_table
from .migration import migration_table
from .remote_server import remote_server_table
from commons.models.b2bi_config import b2bi_config_table
from .validation import validation_table

__all__ = [
    "metadata",
    "server_table",
    "cfttcp_table",
    "cftprot_table",
    "cftssl_table",
    "partner_table",
    "flow_table",
    "processing_table",
    "bosco_route_table",
    "copilot_activity_table",
    "migration_table",
    "remote_server_table",
    "b2bi_config_table",
    "validation_table",
]
