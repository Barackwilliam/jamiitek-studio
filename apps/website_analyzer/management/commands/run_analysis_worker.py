import time

from django.core.management.base import BaseCommand

from apps.website_analyzer.jobs import claim_next_analysis, fail_stale_analyses, run_analysis


class Command(BaseCommand):
    help = "Process queued website analyses. Run it in a separate terminal next to the web server."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once", action="store_true", help="Process queued analyses, then exit."
        )
        parser.add_argument(
            "--poll-interval", type=float, default=3.0,
            help="Seconds to wait between checks when nothing is queued (default: 3).",
        )

    def handle(self, *args, once=False, poll_interval=3.0, **options):
        stale = fail_stale_analyses()
        if stale:
            self.stdout.write(f"Marked {stale} interrupted analysis(es) as failed.")
        self.stdout.write("Analysis worker started. Press Ctrl+C to stop.")
        try:
            while True:
                analysis = claim_next_analysis()
                if analysis is None:
                    if once:
                        return
                    time.sleep(poll_interval)
                    continue
                self.stdout.write(f"Analyzing {analysis.start_url} (analysis {analysis.pk})...")
                analysis = run_analysis(analysis)
                self.stdout.write(
                    f"Finished analysis {analysis.pk}: {analysis.status}, "
                    f"{analysis.pages_succeeded}/{analysis.pages_attempted} pages."
                )
        except KeyboardInterrupt:
            self.stdout.write("Analysis worker stopped.")
