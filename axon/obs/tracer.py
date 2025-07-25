from __future__ import annotations

import traceback
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime

from .records import ErrorRecord, RunRecord

_current_run: ContextVar[RunRecord | None] = ContextVar("current_run", default=None)


def current_run() -> RunRecord | None:
    return _current_run.get()


@contextmanager
def run_tracer(mode: str, **meta) -> Generator[RunRecord, None, None]:
    record = RunRecord(id=str(uuid.uuid4()), started_at=datetime.utcnow(), mode=mode, **meta)
    token = _current_run.set(record)
    try:
        yield record
    except Exception as exc:  # noqa: BLE001 - re-raise after recording
        record.error = ErrorRecord(
            type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc()
        )
        raise
    finally:
        record.ended_at = datetime.utcnow()
        _current_run.reset(token)
