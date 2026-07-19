"""Ship application logs to Grafana Loki via its HTTP push API.

Opt-in: nothing happens unless LOKI_URL is set. The handler is non-blocking —
log records are queued and shipped in batches by a background thread, so a slow
or unreachable Loki never blocks a request. Shipping failures are reported to
stderr and never raise back into the app (and never loop back through logging).

Env vars:
    LOKI_URL        Loki push endpoint, e.g. https://loki.mnet.web.id/loki/api/v1/push
    LOKI_LABELS     Comma-separated base labels, e.g. "app=fastapi-auth,env=dev"
    LOKI_USERNAME   Optional HTTP basic-auth user
    LOKI_PASSWORD   Optional HTTP basic-auth password
    LOKI_TENANT_ID  Optional multi-tenant org id (X-Scope-OrgID header)
"""

import atexit
import base64
import json
import logging
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv is optional here
    pass


def _parse_labels(raw):
    """Parse "k1=v1,k2=v2" into a dict, ignoring blanks/malformed pairs."""
    labels = {}
    for pair in (raw or "").split(","):
        pair = pair.strip()
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        if key:
            labels[key] = value
    return labels


class LokiHandler(logging.Handler):
    """A non-blocking logging handler that batches records to Loki."""

    def __init__(
        self,
        url,
        labels=None,
        username=None,
        password=None,
        tenant_id=None,
        batch_size=100,
        flush_interval=2.0,
        queue_size=10000,
        timeout=5.0,
        user_agent=None,
    ):
        super().__init__()
        self.url = url
        self.base_labels = labels or {}
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout

        # A non-default User-Agent is required: Cloudflare (which fronts some
        # Loki endpoints) blocks the stock "Python-urllib/*" agent with a 1010
        # ban, silently dropping every push.
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent or "fastapi-auth-loki/1.0 (+https://github.com/hendisantika)",
        }
        if username:
            raw = f"{username}:{password or ''}".encode()
            self._headers["Authorization"] = "Basic " + base64.b64encode(raw).decode()
        if tenant_id:
            self._headers["X-Scope-OrgID"] = tenant_id

        self._queue = queue.Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._worker = threading.Thread(
            target=self._run, name="loki-log-shipper", daemon=True
        )
        self._worker.start()
        atexit.register(self.close)

    def emit(self, record):
        try:
            entry = (
                int(record.created * 1_000_000_000),  # unix nanoseconds
                self.format(record),
                record.levelname.lower(),
                record.name,
            )
            self._queue.put_nowait(entry)
        except queue.Full:
            # Under sustained backpressure, drop rather than block the app.
            pass
        except Exception:
            self.handleError(record)

    def _run(self):
        batch = []
        last_flush = time.monotonic()
        while not self._stop.is_set():
            timeout = max(0.0, self.flush_interval - (time.monotonic() - last_flush))
            try:
                batch.append(self._queue.get(timeout=timeout))
            except queue.Empty:
                pass
            due = time.monotonic() - last_flush >= self.flush_interval
            if batch and (len(batch) >= self.batch_size or due):
                self._ship(batch)
                batch = []
                last_flush = time.monotonic()

        # Drain whatever is left on shutdown.
        try:
            while True:
                batch.append(self._queue.get_nowait())
        except queue.Empty:
            pass
        if batch:
            self._ship(batch)

    def _ship(self, batch):
        # Group entries into streams keyed by (level, logger) to keep label
        # cardinality low; Loki wants values sorted by timestamp per stream.
        streams = {}
        for ts, line, level, logger_name in batch:
            streams.setdefault((level, logger_name), []).append((ts, line))

        payload = {"streams": []}
        for (level, logger_name), values in streams.items():
            values.sort(key=lambda v: v[0])
            labels = dict(self.base_labels)
            labels["level"] = level
            labels["logger"] = logger_name
            payload["streams"].append(
                {
                    "stream": labels,
                    "values": [[str(ts), line] for ts, line in values],
                }
            )

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=data, headers=self._headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status >= 300:
                    self._report(f"Loki push failed: HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            body = e.read()[:200].decode("utf-8", "replace")
            self._report(f"Loki push failed: HTTP {e.code} {body}")
        except Exception as e:
            self._report(f"Loki push error: {type(e).__name__}: {e}")

    @staticmethod
    def _report(msg):
        # Write directly to stderr so shipping errors never loop back through
        # the logging system (which would feed this handler again).
        print(msg, file=sys.stderr, flush=True)

    def close(self):
        if not self._stop.is_set():
            self._stop.set()
            self._worker.join(timeout=self.timeout + 2)
        super().close()


def init_loki_logging():
    """Attach a Loki handler to the root logger when LOKI_URL is set.

    Returns the handler, or None when Loki logging is disabled.
    """
    log = logging.getLogger("app.loki")

    url = os.getenv("LOKI_URL")
    if not url:
        log.info("Loki logging disabled (LOKI_URL not set)")
        return None

    labels = _parse_labels(os.getenv("LOKI_LABELS"))
    labels.setdefault("app", os.getenv("ELASTIC_APM_SERVICE_NAME", "fastapi-auth-mysql"))

    handler = LokiHandler(
        url=url,
        labels=labels,
        username=os.getenv("LOKI_USERNAME") or None,
        password=os.getenv("LOKI_PASSWORD") or None,
        tenant_id=os.getenv("LOKI_TENANT_ID") or None,
        user_agent=os.getenv("LOKI_USER_AGENT") or None,
    )
    # Log body carries level/logger too; Loki supplies its own timestamp.
    handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    handler.setLevel(getattr(logging, level_name, logging.INFO))

    logging.getLogger().addHandler(handler)
    log.info("Loki logging enabled (url=%s, labels=%s)", url, labels)
    return handler
