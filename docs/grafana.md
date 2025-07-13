# Grafana Dashboard

TEL3SIS ships with a preconfigured Grafana dashboard to visualize Prometheus metrics.

## Access

Browse to [http://localhost:3000/d/tel3sis-latency](http://localhost:3000/d/tel3sis-latency) and log in with the default `admin` / `admin` credentials.
If the dashboard is missing, import `ops/grafana/tel3sis.json` via **Dashboard → Import**.

## Panels

The dashboard includes graphs for:

- STT, LLM and TTS latency (95th percentile)
- HTTP request latency
- External API latency
- Celery task latency
- Task failures per minute

Use the time range controls in the top right to zoom in on recent activity.
