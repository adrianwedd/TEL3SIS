# syntax=docker/dockerfile:1

FROM python:3.13-slim AS builder
WORKDIR /app

# Install build dependencies and create virtualenv
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential libssl-dev \ 
    && python -m venv /opt/venv \ 
    && /opt/venv/bin/pip install --upgrade pip \ 
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13-slim AS runtime
WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
COPY . .

CMD ["sleep", "infinity"]
