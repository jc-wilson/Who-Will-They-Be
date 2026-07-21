import json
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


LOG_FILE_PREFIX = "valscanner_"
LOG_FILE_SUFFIX = ".jsonl"
DEFAULT_MAX_LOG_FILES = 3
_SENSITIVE_KEYS = {
    "authorization",
    "x-riot-entitlements-jwt",
    "x-riot-clientplatform",
    "access_token",
    "accesstoken",
    "entitlement_token",
    "entitlementtoken",
    "token",
    "password",
    "auth",
    "headers",
}
_SENSITIVE_QUERY_KEYS = {"access_token", "token", "password", "auth"}
_SECRET_REPLACEMENTS = (
    (re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"Basic\s+[A-Za-z0-9+/=-]+", re.IGNORECASE), "Basic [REDACTED]"),
)
_ALLOWED_EVENT_PREFIXES = ("xmpp_",)
_ALLOWED_EVENTS = {
    "runtime_log_started",
}
_SUPPRESSED_XMPP_EVENTS = {
    "xmpp_chunk",
    "xmpp_rewrite",
    "xmpp_domain_detected",
    "xmpp_presence_seen_unchanged",
}

_lock = threading.RLock()
_log_path = None
_session_id = None
_max_log_files = DEFAULT_MAX_LOG_FILES


def get_app_root(base_path=None):
    if base_path is not None:
        return Path(base_path)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_logs_dir(base_path=None):
    return get_app_root(base_path=base_path) / "logs"


def _new_log_path(logs_dir: Path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = logs_dir / f"{LOG_FILE_PREFIX}{timestamp}{LOG_FILE_SUFFIX}"
    if not candidate.exists():
        return candidate

    suffix = 1
    while True:
        candidate = logs_dir / f"{LOG_FILE_PREFIX}{timestamp}_{suffix}{LOG_FILE_SUFFIX}"
        if not candidate.exists():
            return candidate
        suffix += 1


def _rotate_logs(logs_dir: Path, keep: int, current_path: Path):
    log_files = sorted(
        logs_dir.glob(f"{LOG_FILE_PREFIX}*{LOG_FILE_SUFFIX}"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for old_path in log_files[keep:]:
        if old_path == current_path:
            continue
        try:
            old_path.unlink()
        except OSError:
            pass


def initialize_runtime_logging(base_path=None, app_version=None, max_log_files=DEFAULT_MAX_LOG_FILES):
    global _log_path, _session_id, _max_log_files
    with _lock:
        _max_log_files = max(1, int(max_log_files or DEFAULT_MAX_LOG_FILES))
        logs_dir = get_logs_dir(base_path=base_path)
        logs_dir.mkdir(parents=True, exist_ok=True)
        _log_path = _new_log_path(logs_dir)
        _session_id = _log_path.stem
        _log_path.touch(exist_ok=False)
        _rotate_logs(logs_dir, _max_log_files, _log_path)

    log_event(
        "runtime_log_started",
        app_version=app_version,
        app_root=str(get_app_root(base_path=base_path)),
        logs_dir=str(logs_dir),
        log_file=str(_log_path),
        frozen=bool(getattr(sys, "frozen", False)),
    )
    return _log_path


def get_log_file_path():
    with _lock:
        if _log_path is None:
            initialize_runtime_logging()
        return _log_path


def reset_runtime_logging_for_tests():
    global _log_path, _session_id, _max_log_files
    with _lock:
        _log_path = None
        _session_id = None
        _max_log_files = DEFAULT_MAX_LOG_FILES


def sanitize_url(url):
    text = str(url or "")
    if not text:
        return text
    try:
        parts = urlsplit(text)
        if not parts.query:
            return _redact_string(text)
        query = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            if key.lower() in _SENSITIVE_QUERY_KEYS:
                query.append((key, "[REDACTED]"))
            else:
                query.append((key, value))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    except Exception:
        return _redact_string(text)


def sanitize_value(value):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in _SENSITIVE_KEYS:
                sanitized[key_text] = "[REDACTED]"
            elif key_text.lower() == "url":
                sanitized[key_text] = sanitize_url(item)
            else:
                sanitized[key_text] = sanitize_value(item)
        return sanitized
    if isinstance(value, (list, tuple, set)):
        return [sanitize_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return response_preview(value.decode("utf-8", errors="replace"))
    if isinstance(value, str):
        return _redact_string(value)
    return value


def _redact_string(value: str):
    redacted = value
    for pattern, replacement in _SECRET_REPLACEMENTS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def response_preview(body, limit=500):
    preview = " ".join(str(body or "").split())
    preview = sanitize_value(preview)
    if len(preview) > limit:
        return f"{preview[:limit]}..."
    return preview or "<empty>"


def log_event(event_type, **fields):
    try:
        event_name = str(event_type)
        if not _should_write_event(event_name):
            return
        with _lock:
            path = get_log_file_path() if _log_path is None else _log_path
            record = {
                "time": datetime.now().isoformat(timespec="milliseconds"),
                "timestamp": time.time(),
                "session": _session_id,
                "event": event_name,
            }
            record.update(sanitize_value(fields))
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _should_write_event(event_name):
    if event_name in _SUPPRESSED_XMPP_EVENTS:
        return False
    if event_name in _ALLOWED_EVENTS:
        return True
    return event_name.startswith(_ALLOWED_EVENT_PREFIXES)


def log_exception(event_type, exc, **fields):
    log_event(
        event_type,
        error_type=type(exc).__name__,
        error=str(exc),
        traceback="".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        **fields,
    )
