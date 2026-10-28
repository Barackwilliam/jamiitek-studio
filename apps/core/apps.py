from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        from .db_security import enable_rls_after_migrate

        # post_migrate fires once per app; a fixed dispatch_uid keeps a
        # single receiver, and the handler itself is idempotent.
        post_migrate.connect(enable_rls_after_migrate, dispatch_uid="core.enable_rls")
