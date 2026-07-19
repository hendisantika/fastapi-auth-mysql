#!/usr/bin/env python3
"""Standalone Elastic APM connectivity/credential checker.

Talks to the APM server directly (no FastAPI involved) and reports, step by
step, whether the endpoint is reachable, whether the credentials are accepted,
and whether a test transaction is ingested (HTTP 202). Use it to distinguish a
wrong-URL / wrong-deployment problem from an auth problem.

Usage:
    python verify_apm.py

Reads the same env vars the app uses (from the shell or a local .env):
    ELASTIC_APM_SERVER_URL      (required)
    ELASTIC_APM_SECRET_TOKEN    (use this OR the API key)
    ELASTIC_APM_API_KEY
    ELASTIC_APM_SERVICE_NAME    (default: fastapi-auth-mysql)
    ELASTIC_APM_ENVIRONMENT     (default: verify-script)
"""

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv is optional for this script
    pass


def _c(code):
    return code if sys.stdout.isatty() else ""


GREEN, RED, YELLOW, DIM, RESET = (
    _c("\033[32m"),
    _c("\033[31m"),
    _c("\033[33m"),
    _c("\033[2m"),
    _c("\033[0m"),
)


def ok(msg):
    print(f"{GREEN}PASS{RESET}  {msg}")


def fail(msg):
    print(f"{RED}FAIL{RESET}  {msg}")


def warn(msg):
    print(f"{YELLOW}WARN{RESET}  {msg}")


def auth_header():
    """Return the Authorization header value, preferring the secret token."""
    token = os.getenv("ELASTIC_APM_SECRET_TOKEN")
    api_key = os.getenv("ELASTIC_APM_API_KEY")
    if token:
        return f"Bearer {token}", "secret token"
    if api_key:
        return f"ApiKey {api_key}", "API key"
    return None, "none"


def request(url, method="GET", data=None, headers=None, timeout=15):
    """Perform an HTTP request, returning (status, body) without raising on 4xx/5xx."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        return None, f"{type(e.reason).__name__ if e.reason else 'URLError'}: {e.reason}"
    except Exception as e:  # timeouts, SSL errors, etc.
        return None, f"{type(e).__name__}: {e}"


def main():
    server_url = os.getenv("ELASTIC_APM_SERVER_URL")
    service_name = os.getenv("ELASTIC_APM_SERVICE_NAME", "fastapi-auth-mysql")
    environment = os.getenv("ELASTIC_APM_ENVIRONMENT", "verify-script")

    print(f"{DIM}Elastic APM connection check{RESET}")
    print("=" * 60)

    if not server_url:
        fail("ELASTIC_APM_SERVER_URL is not set — nothing to test.")
        print("      Set it in your environment or .env and re-run.")
        return 2

    base = server_url.rstrip("/")
    header, kind = auth_header()
    print(f"Server URL   : {base}")
    print(f"Service name : {service_name}")
    print(f"Environment  : {environment}")
    print(f"Credential   : {kind}")
    if not header:
        warn("No secret token or API key set — the server will likely reject data.")
    print("-" * 60)

    # ---- Step 1: reachability + auth via the server info endpoint ----------
    # APM Server root returns 200 with build info when the credential is valid.
    status, body = request(base + "/", headers={"Authorization": header} if header else {})
    if status is None:
        fail(f"Cannot reach the APM server: {body}")
        print("      -> Check the URL/port, DNS, firewall, or that the")
        print("         deployment's Integrations/APM server is running.")
        return 1
    if status == 200:
        info = ""
        try:
            info = " " + json.dumps(json.loads(body))[:160]
        except Exception:
            pass
        ok(f"APM server reachable and credential accepted (HTTP 200).{DIM}{info}{RESET}")
    elif status == 401:
        fail("HTTP 401 — the credential was rejected (bad/misencoded token or key).")
        print("      -> Prefer a SECRET TOKEN from the deployment's APM 'Add data'")
        print("         page. If using an API key it must be base64(id:api_key).")
        return 1
    elif status == 403:
        fail("HTTP 403 — authenticated but not authorized to write APM data.")
        return 1
    elif status == 404:
        warn("HTTP 404 at '/' — reachable but this may not be an APM server URL.")
        print(f"      Body: {body[:200]}")
    else:
        warn(f"Unexpected HTTP {status} at '/': {body[:200]}")

    # ---- Step 2: send a real test transaction to the intake endpoint -------
    intake = base + "/intake/v2/events"
    txn_id = os.urandom(8).hex()
    trace_id = os.urandom(16).hex()
    now_us = int(time.time() * 1_000_000)

    metadata = {
        "metadata": {
            "service": {
                "name": service_name,
                "environment": environment,
                "agent": {"name": "python", "version": "verify-script"},
                "language": {"name": "python"},
            }
        }
    }
    transaction = {
        "transaction": {
            "id": txn_id,
            "trace_id": trace_id,
            "name": "GET /verify-apm-connection",
            "type": "request",
            "duration": 1.5,
            "timestamp": now_us,
            "result": "HTTP 2xx",
            "sampled": True,
            "span_count": {"started": 0},
        }
    }
    ndjson = (json.dumps(metadata) + "\n" + json.dumps(transaction) + "\n").encode()

    headers = {"Content-Type": "application/x-ndjson"}
    if header:
        headers["Authorization"] = header
    status, body = request(intake, method="POST", data=ndjson, headers=headers)

    print("-" * 60)
    if status == 202:
        ok("Test transaction ACCEPTED by the APM server (HTTP 202).")
        print(f"      service={service_name!r} environment={environment!r}")
        print(f"      trace_id={trace_id}")
        print()
        print("      If this service still does not appear in Kibana APM, you are")
        print("      almost certainly looking at a DIFFERENT deployment than the")
        print("      one this APM URL belongs to. Open the deployment that owns")
        print("      this APM endpoint and check its own Kibana, and widen the")
        print("      time range to include now.")
        return 0
    if status is None:
        fail(f"Could not POST to the intake endpoint: {body}")
        return 1
    if status in (401, 403):
        fail(f"Intake rejected the credential (HTTP {status}).")
        print(f"      Body: {body[:300]}")
        return 1
    if status == 400:
        warn(f"HTTP 400 from intake (payload issue), but connectivity+auth are OK.")
        print(f"      Body: {body[:300]}")
        return 0
    fail(f"Unexpected HTTP {status} from intake endpoint.")
    print(f"      Body: {body[:300]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
