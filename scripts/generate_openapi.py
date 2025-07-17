#!/usr/bin/env python
"""Generate OpenAPI schema for TEL3SIS."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> None:
    """Write OpenAPI schema to docs/openapi.json."""
    os.environ.setdefault("SECRET_KEY", "changeme")
    os.environ.setdefault("BASE_URL", "http://localhost")
    os.environ.setdefault("TWILIO_ACCOUNT_SID", "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
    os.environ.setdefault("TWILIO_AUTH_TOKEN", "secret")
    os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "MTIzNDU2Nzg5MDEyMzQ1Ng==")

    sys.path.append(str(Path(__file__).resolve().parents[1]))

    from tests.utils import vocode_mocks

    vocode_mocks.install()

    from fastapi.openapi.utils import get_openapi
    from server.app import create_app
    from server.settings import Settings

    cfg = Settings()
    app = create_app(cfg)
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    out_path = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
    out_path.write_text(json.dumps(schema, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
