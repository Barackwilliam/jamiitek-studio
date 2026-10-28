import shutil
import tempfile
import time
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.ratelimit import delete_old_events

TEMP_PREFIX = "jamiitek-tmp-"  # only folders this application created
TEMP_MAX_AGE_SECONDS = 6 * 3600
RECENT_FILE_SECONDS = 3600


def referenced_files():
    """Every stored file name a database row still points to."""
    from apps.creative_assets.models import Asset, Poster
    from apps.media_production.models import AudioTrack, VideoRender

    names = set()
    for model, fields in [(Asset, ["file", "thumbnail"]), (Poster, ["file"]),
                          (AudioTrack, ["file"]), (VideoRender, ["file"])]:
        for row in model.objects.values_list(*fields):
            names.update(name for name in row if name)
    return names


def stored_files(storage, folder="projects"):
    try:
        directories, files = storage.listdir(folder)
    except (FileNotFoundError, NotADirectoryError, OSError):
        return
    for name in files:
        yield f"{folder}/{name}"
    for directory in directories:
        yield from stored_files(storage, f"{folder}/{directory}")


def _is_recent(storage, name, max_age=RECENT_FILE_SECONDS):
    try:
        modified = storage.get_modified_time(name)
    except (NotImplementedError, OSError):
        return True  # cannot tell: keep it
    return (timezone.now() - modified).total_seconds() < max_age


def stale_temp_folders(max_age=TEMP_MAX_AGE_SECONDS):
    cutoff = time.time() - max_age
    for path in Path(tempfile.gettempdir()).glob(f"{TEMP_PREFIX}*"):
        try:
            if path.is_dir() and path.stat().st_mtime < cutoff:
                yield path
        except OSError:
            continue


class Command(BaseCommand):
    help = ("Find leftover temporary folders and stored files that no record uses. "
            "Shows what would be removed; add --delete to remove it.")

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Actually remove the files listed.")

    def handle(self, *args, delete=False, **options):
        verb = "Removed" if delete else "Would remove"

        temp = list(stale_temp_folders())
        for path in temp:
            if delete:
                shutil.rmtree(path, ignore_errors=True)
        self.stdout.write(f"{verb} {len(temp)} leftover temporary folder(s).")

        # A new file is saved a moment before its database row, so recent
        # files are skipped: they may belong to an upload or render in progress.
        keep = referenced_files()
        orphans = [name for name in stored_files(default_storage)
                   if name not in keep and not _is_recent(default_storage, name)]
        for name in orphans:
            self.stdout.write(f"  orphan: {name}")
            if delete:
                default_storage.delete(name)
        self.stdout.write(f"{verb} {len(orphans)} stored file(s) that no record uses.")

        if delete:
            removed = delete_old_events()
            self.stdout.write(f"Removed {removed} old rate-limit record(s).")
        if not delete and (temp or orphans):
            self.stdout.write("Nothing was deleted. Run again with --delete to remove these.")
