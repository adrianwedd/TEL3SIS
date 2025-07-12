# Production Deployment Guide

This guide outlines the recommended setup for running TEL3SIS in a
production environment. It focuses on scaling Celery workers,
keeping the database and message broker reliable, and shows example
environment variables.

## Celery Worker Pool

Run multiple Celery worker instances to process tasks concurrently.
Each worker can handle a configurable number of processes:

```bash
celery -A server.celery_app worker --concurrency=4 --loglevel=info
```

Scale horizontally by starting additional workers and consider using
separate queues for long‑running jobs. Monitor the workload with
`celery inspect` and adjust the number of workers as traffic grows.

## Database Connection Pooling

Use **PgBouncer** in front of PostgreSQL to handle many short‑lived
connections created by Celery tasks and the FastAPI app.

1. Run PgBouncer on the same network as your database.
2. Point `DATABASE_URL` to the PgBouncer port, e.g.
   `postgresql://user:pass@pgbouncer:6432/dbname`.
3. Tune `default_pool_size` and `max_client_conn` based on expected
   concurrency.

PgBouncer minimizes connection overhead and keeps the database stable
under load.

## Redis High Availability

TEL3SIS uses Redis for Celery and state management. For production,
configure **Redis Sentinel** or **Redis Cluster** to avoid single
points of failure.

- **Redis Sentinel** provides automatic failover for a primary/replica
  setup. Update `REDIS_URL`, `CELERY_BROKER_URL`, and
  `CELERY_RESULT_BACKEND` to point to the Sentinel endpoints.
- **Redis Cluster** shards data across multiple nodes. Use when you
  require scaling beyond a single instance.

Set the environment variables accordingly. Example using Sentinel:

```bash
REDIS_URL=redis://mymaster/0
CELERY_BROKER_URL=redis://mymaster/0
CELERY_RESULT_BACKEND=redis://mymaster/1
```

## Example Environment Settings

A minimal `.env` for a production deployment might include:

```bash
BASE_URL=https://tel3sis.example.com
DATABASE_URL=postgresql://user:pass@pgbouncer:6432/tel3sis
REDIS_URL=redis://mymaster/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_WORKER_CONCURRENCY=4
```

Override `CELERY_WORKER_CONCURRENCY` when starting each worker to scale
up or down without changing the image.

## Scaling Notes

- Start with at least two Celery workers so that one can take over if
the other stops. Increase the `--concurrency` value or add more
workers as call volume rises.
- PgBouncer reduces connection churn and allows the database to handle
hundreds of worker processes efficiently.
- Redis Sentinel or Cluster protects against broker outages. Always
deploy at least three Sentinel nodes or six Cluster nodes for quorum.

A typical production stack runs behind a load balancer (e.g. Nginx or
a cloud ingress) with the above services on managed infrastructure.
This architecture supports horizontal scaling as traffic demands.

