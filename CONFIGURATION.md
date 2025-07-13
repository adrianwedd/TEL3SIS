# Configuration Reference

TEL3SIS loads all settings from environment variables (typically via a `.env` file).
The table below lists each variable, whether it is required, and its default value if optional.

| Variable | Required? | Default | Description |
|---------|-----------|---------|-------------|
| `SECRET_KEY` | Yes | – | Session signing key for FastAPI. |
| `BASE_URL` | Yes | – | Public webhook URL reachable by Twilio. |
| `TWILIO_ACCOUNT_SID` | Yes | – | Twilio account ID for inbound/outbound calls. |
| `TWILIO_AUTH_TOKEN` | Yes | – | Twilio auth token. |
| `TOKEN_ENCRYPTION_KEY` | Yes | – | Base64 AES key for encrypting OAuth tokens. |
| `OPENAI_API_KEY` | No | "" | API key for OpenAI models. |
| `ELEVEN_LABS_API_KEY` | No | "" | API key for ElevenLabs TTS. |
| `EMBEDDING_PROVIDER` | No | `sentence_transformers` | Embedding backend (`openai` or `sentence_transformers`). |
| `EMBEDDING_MODEL_NAME` | No | `all-MiniLM-L6-v2` | Model name for sentence-transformers embeddings. |
| `OPENAI_EMBEDDING_MODEL` | No | `text-embedding-3-small` | Model when using OpenAI embeddings. |
| `OPENAI_MODEL` | No | `gpt-3.5-turbo` | Chat model for conversations. |
| `OPENAI_SAFETY_MODEL` | No | `gpt-3.5-turbo` | Model used for safety analysis. |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection used by Celery and state. |
| `CELERY_BROKER_URL` | No | uses `REDIS_URL` | Celery message broker URL. |
| `CELERY_RESULT_BACKEND` | No | uses `CELERY_BROKER_URL` | Celery result backend. |
| `DATABASE_URL` | No | `sqlite:///tel3sis.db` | SQLAlchemy database URL. |
| `ESCALATION_PHONE_NUMBER` | No | "" | Number dialed when escalating a call. |
| `CALL_RATE_LIMIT` | No | `3/minute` | Rate limit for inbound calls per host. |
| `API_RATE_LIMIT` | No | `60/minute` | Rate limit for REST API requests. |
| `OAUTH_AUTH_URL` | No | `https://example.com/auth` | OAuth authorization endpoint. |
| `GOOGLE_CLIENT_ID` | No | "" | Google OAuth client ID for Calendar access. |
| `GOOGLE_CLIENT_SECRET` | No | "" | Google OAuth client secret. |
| `SENDGRID_API_KEY` | No | "" | SendGrid API key for email notifications. |
| `SENDGRID_FROM_EMAIL` | No | "" | Sender address for SendGrid emails. |
| `NOTIFY_EMAIL` | No | "" | Recipient address for call transcripts. |
| `VECTOR_DB_PATH` | No | `vector_store` | Directory for vector embeddings. |
| `BACKUP_DIR` | No | `backups` | Directory for local backup archives. |
| `BACKUP_S3_BUCKET` | No | "" | S3 bucket used when uploading backups. |
| `SLACK_WEBHOOK_URL` | No | "" | Slack webhook for alert notifications. |
| `PAGERDUTY_ROUTING_KEY` | No | "" | PagerDuty routing key for alerts. |
| `LOG_LEVEL` | No | `INFO` | Log output level. |
| `LOG_ROTATION` | No | `10 MB` | Log file rotation size. |
| `LOG_FILE` | No | `logs/tel3sis.log` | Path to persistent log file. |
| `CELERY_WORKER_CONCURRENCY` | No | none | Worker processes per Celery instance. |

`CELERY_WORKER_CONCURRENCY` is not read by the application directly but is commonly
used when starting workers in production. Values left empty in the table
indicate the feature is disabled unless populated.
