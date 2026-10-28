"""Row level security for Django tables on PostgreSQL.

Supabase exposes tables through its Data API to the `anon` and
`authenticated` roles. Django does not use that API: it connects directly as
the role that owns its tables. Enabling (not forcing) row level security
without any policies therefore blocks the Data API roles completely while
leaving Django unaffected, because PostgreSQL does not apply RLS to a
table's owner.
"""

import logging

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

TABLES_WITHOUT_RLS_SQL = """
    SELECT c.relname
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind IN ('r', 'p')
      AND n.nspname = current_schema()
      AND c.relowner = (SELECT oid FROM pg_roles WHERE rolname = current_user)
      AND NOT c.relrowsecurity
    ORDER BY c.relname
"""


def enable_row_level_security(using="default"):
    """Enable RLS on every table owned by Django's role. Returns table names changed."""
    connection = connections[using]
    if connection.vendor != "postgresql" or not getattr(settings, "POSTGRES_ENABLE_RLS", True):
        return []
    changed = []
    with connection.cursor() as cursor:
        cursor.execute(TABLES_WITHOUT_RLS_SQL)
        for (table,) in cursor.fetchall():
            cursor.execute(
                f"ALTER TABLE {connection.ops.quote_name(table)} ENABLE ROW LEVEL SECURITY"
            )
            changed.append(table)
    if changed:
        logger.info("Enabled row level security on %d table(s).", len(changed))
    return changed


def enable_rls_after_migrate(sender, using="default", **kwargs):
    enable_row_level_security(using=using)
