"""A small registry of background job types for `manage.py run_worker`.

Each app registers a handler in its AppConfig.ready(). The worker takes one
job from each handler in turn, so a long analysis queue cannot starve AI
generation or the other way round.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class JobHandler:
    name: str
    claim: object        # () -> job or None; must claim atomically
    run: object          # (job) -> job; must record failures itself
    fail_stale: object   # () -> number of interrupted jobs marked failed
    describe: object     # (job) -> short text for the console


_handlers = []


def register(handler):
    if all(existing.name != handler.name for existing in _handlers):
        _handlers.append(handler)


def handlers():
    return list(_handlers)
