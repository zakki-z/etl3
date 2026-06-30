from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class ViewBase(DeclarativeBase):
    """Declarative base for MySQL VIEWs (v_cft_flow_xlate_enabled, v_cft_partner_ssl_enabled, ...).

    Deliberately separate from `Base` in db.py. `init_database()` only calls
    `Base.metadata.create_all()` — if a view-mapped class used that same Base,
    create_all() would try to `CREATE TABLE` over a name that already exists
    as a VIEW and fail. Classes mapped against ViewBase are never created or
    altered by application code; they exist purely so routers/services get
    typed, read-only access to data the DB already computes via the view's
    own SELECT. Never insert/update/delete through a ViewBase model.
    """

    pass
