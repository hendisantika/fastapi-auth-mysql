# Grafana

Starter dashboard for the logs this app ships to Grafana Loki (see
[`loki_logging.py`](../loki_logging.py) and the **Logs (Grafana Loki)** section
of the main [README](../README.md)).

## Dashboard: FastAPI Auth — Logs (Loki)

File: [`dashboards/fastapi-auth-loki.json`](dashboards/fastapi-auth-loki.json)

Panels:

- **Overview** — stat tiles: total logs, errors, warnings, requests (over the
  selected time range).
- **Log volume by level** — stacked count of log lines per level over time.
- **Requests by status** — request count grouped by HTTP status code, parsed
  from the `app.request` log lines.
- **Request latency** — p50 / p90 / p99 response time (ms), parsed from the
  request logs.
- **Top endpoints** — the busiest paths by request count.
- **Application logs** — live log stream, filterable by level.

Template variables: **datasource** (pick your Loki source), **App**, **Env**,
**Level**.

### Import

1. In Grafana, go to **Dashboards → New → Import**.
2. Upload `dashboards/fastapi-auth-loki.json` (or paste its contents).
3. When prompted, select your **Loki** data source.
4. Save. Adjust the **App** / **Env** variables at the top (deployed app uses
   `app=fastapi-auth, env=dev`; local runs use `app=fastapi-auth-mysql,
   env=local`).

### Notes

- The status/latency/endpoint panels parse the request log line
  (`GET /path from <ip> -> <status> (<ms>ms)`) with a LogQL `regexp` stage, so
  they depend on the log format emitted by the request-logging middleware in
  [`main.py`](../main.py). If that format changes, update the `regexp` in the
  affected panels.
- Errors/warnings tiles read `level="error"` / `level="warning"` labels, which
  the Loki handler sets from each record's log level.
