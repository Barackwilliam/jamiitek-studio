from apps.core.management.commands.run_worker import Command as WorkerCommand


class Command(WorkerCommand):
    help = "Older name for run_worker, kept so existing instructions keep working."
