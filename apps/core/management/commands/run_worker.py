import logging
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections, connection
from django.utils import timezone

from apps.core.models import WorkerHeartbeat
from apps.core.worker import handlers

logger = logging.getLogger(__name__)

ERROR_PAUSE_SECONDS = 10


class Command(BaseCommand):
    help = ("Process background jobs (website analysis, AI writing, image imports and videos). "
            "Run it in a separate terminal next to the web server.")

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process queued jobs, then exit.")
        parser.add_argument(
            "--poll-interval", type=float, default=3.0,
            help="Seconds to wait between checks when nothing is queued (default: 3).",
        )

    def _beat(self, processed=0, error=False):
        heartbeat, _created = WorkerHeartbeat.objects.get_or_create(
            name="default", defaults={"last_seen": timezone.now()})
        heartbeat.last_seen = timezone.now()
        heartbeat.jobs_processed += processed
        if error:
            heartbeat.last_error_at = timezone.now()
        heartbeat.save()

    def _process_one_round(self):
        """Give every handler one chance to run a job. Returns (jobs_done, had_error)."""
        done, had_error = 0, False
        for handler in handlers():
            try:
                job = handler.claim()
                if job is None:
                    continue
                self.stdout.write(f"Starting {handler.name}: {handler.describe(job)}")
                job = handler.run(job)
                done += 1
                self.stdout.write(f"Finished {handler.name}: {handler.describe(job)} -> {job.status}")
            except Exception:
                # Handlers record expected failures themselves; anything that
                # reaches here is unexpected (for example the database being
                # briefly unavailable). Log it and keep the worker alive.
                logger.exception("Worker error in %s", handler.name)
                self.stderr.write(f"Error in {handler.name}; see the log. Continuing.")
                had_error = True
        return done, had_error

    def handle(self, *args, once=False, poll_interval=3.0, **options):
        for handler in handlers():
            stale = handler.fail_stale()
            if stale:
                self.stdout.write(f"Marked {stale} interrupted {handler.name} job(s) as failed.")
        self.stdout.write("Worker started. Press Ctrl+C to stop.")
        try:
            while True:
                # Drop broken or expired database connections between rounds, as
                # Django does between web requests. Never inside a transaction.
                if not connection.in_atomic_block:
                    close_old_connections()
                done, had_error = self._process_one_round()
                try:
                    self._beat(processed=done, error=had_error)
                except Exception:
                    logger.exception("Could not record worker heartbeat")
                if had_error:
                    if once:
                        return
                    time.sleep(ERROR_PAUSE_SECONDS)
                elif not done:
                    if once:
                        return
                    time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.stdout.write("Worker stopped.")
