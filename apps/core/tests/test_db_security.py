"""Tests for automatic row level security on PostgreSQL.

These run against PostgreSQL only when the test database is PostgreSQL
(DATABASE_URL is set); on SQLite they verify the safe no-op.
"""

import unittest

from django.db import connection
from django.test import TestCase

from apps.core.db_security import enable_row_level_security


class SQLiteRLSTests(TestCase):
    @unittest.skipIf(connection.vendor == "postgresql", "SQLite-only behaviour")
    def test_is_a_no_op_on_sqlite(self):
        self.assertEqual(enable_row_level_security(), [])


@unittest.skipUnless(connection.vendor == "postgresql", "requires PostgreSQL")
class PostgresRLSTests(TestCase):
    def table_has_rls(self, table):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT relrowsecurity FROM pg_class WHERE relname = %s "
                "AND relnamespace = current_schema()::regnamespace",
                [table],
            )
            return cursor.fetchone()[0]

    def test_all_django_tables_have_rls_after_migrate(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT relname FROM pg_class WHERE relkind = 'r' "
                "AND relnamespace = current_schema()::regnamespace AND NOT relrowsecurity"
            )
            without_rls = [row[0] for row in cursor.fetchall()]

        self.assertEqual(without_rls, [])
        self.assertTrue(self.table_has_rls("projects_project"))

    def test_new_tables_are_covered_and_call_is_idempotent(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE rls_probe (id int)")

        self.assertEqual(enable_row_level_security(), ["rls_probe"])
        self.assertTrue(self.table_has_rls("rls_probe"))
        self.assertEqual(enable_row_level_security(), [])

    def test_django_can_still_read_and_write_with_rls_enabled(self):
        from django.contrib.auth import get_user_model

        from apps.projects.models import Project

        user = get_user_model().objects.create_user("rls-user", password="x-pass-123!")
        Project.objects.create(owner=user, name="Visible to Django")

        self.assertEqual(Project.objects.filter(name="Visible to Django").count(), 1)
