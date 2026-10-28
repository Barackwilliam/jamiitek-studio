import time

from django.core.management.base import BaseCommand

from apps.core.worker import handlers


class Command(BaseCommand):
    help = ("Process background jobs (website analysis and AI writing). "
            "Run it in a separate terminal next to the web server.")

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Process queued jobs, then exit.")
        parser.add_argument(
            "--poll-interval", type=float, default=3.0,
            help="Seconds to wait between checks when nothing is queued (default: 3).",
        )

    def handle(self, *args, once=False, poll_interval=3.0, **options):
        for handler in handlers():
            stale = handler.fail_stale()
            if stale:
                self.stdout.write(f"Marked {stale} interrupted {handler.name} job(s) as failed.")
        self.stdout.write("Worker started. Press Ctrl+C to stop.")
        try:
            while True:
                did_work = False
                for handler in handlers():
                    job = handler.claim()
                    if job is None:
                        continue
                    did_work = True
                    self.stdout.write(f"Starting {handler.name}: {handler.describe(job)}")
                    job = handler.run(job)
                    self.stdout.write(f"Finished {handler.name}: {handler.describe(job)} -> {job.status}")
                if not did_work:
                    if once:
                        return
                    time.sleep(poll_interval)
        except KeyboardInterrupt:
            self.stdout.write("Worker stopped.")
