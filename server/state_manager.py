from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, Optional, List, Iterable, cast

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import redis

from .vector_db import VectorDB
from .config import Config, ConfigError


class StateManager:
    """Simple wrapper around Redis for call session state."""

    def __init__(
        self,
        url: Optional[str] = None,
        prefix: str = "session",
        *,
        summary_db: Optional[VectorDB] = None,
    ) -> None:
        cfg = Config()
        self.url = url or cfg.redis_url
        self.prefix = prefix
        self._redis = redis.Redis.from_url(self.url, decode_responses=True)

        self._summary_db = summary_db or VectorDB(collection_name="summaries")

        self._encryption_key = self._load_encryption_key(cfg.token_encryption_key)

    def _load_encryption_key(self, key_b64: str) -> bytes:
        """Return the AES key from ``TOKEN_ENCRYPTION_KEY`` env variable."""
        if not key_b64:
            raise ConfigError(
                "Missing required environment variable: TOKEN_ENCRYPTION_KEY"
            )
        try:
            key_bytes = base64.b64decode(key_b64)
        except Exception as exc:  # pragma: no cover - invalid base64 rare
            raise ConfigError("Invalid TOKEN_ENCRYPTION_KEY format") from exc
        if len(key_bytes) != 16:
            raise ConfigError(
                "TOKEN_ENCRYPTION_KEY must decode to 16 bytes (128-bit AES key)"
            )
        return key_bytes

    def _key(self, call_sid: str) -> str:
        return f"{self.prefix}:{call_sid}"

    def _token_key(self, user_id: str) -> str:
        return f"token:{user_id}"

    def _oauth_key(self, state: str) -> str:
        return f"oauth:{state}"

    def _encrypt(self, data: str) -> str:
        aesgcm = AESGCM(self._encryption_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def _decrypt(self, blob: str) -> str:
        raw = base64.b64decode(blob)
        nonce, ciphertext = raw[:12], raw[12:]
        aesgcm = AESGCM(self._encryption_key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

    def create_session(
        self, call_sid: str, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a new session key with optional initial data."""
        if data is None:
            data = {}
        key = self._key(call_sid)
        pipe = self._redis.pipeline()
        if data:
            pipe.hset(key, mapping=data)
        from_number = data.get("from")
        if from_number:
            sims = self._summary_db.search(
                "",
                where={"from_number": from_number},
                n_results=3,
            )
            if sims:
                pipe.hset(key, "similar_summaries", json.dumps(sims))
        pipe.execute()

    def get_session(self, call_sid: str) -> Dict[str, str]:
        """Return all fields for a session."""
        return self._redis.hgetall(self._key(call_sid))

    def update_session(self, call_sid: str, **fields: Any) -> None:
        """Update fields in a session."""
        if fields:
            self._redis.hset(self._key(call_sid), mapping=fields)

    def delete_session(self, call_sid: str) -> None:
        """Remove a session completely."""
        self._redis.delete(self._key(call_sid))

    # --- Token CRUD -------------------------------------------------

    def set_token(
        self,
        user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[int] = None,
    ) -> None:
        data: Dict[str, Any] = {"access_token": access_token}
        if refresh_token is not None:
            data["refresh_token"] = refresh_token
        if expires_at is not None:
            data["expires_at"] = str(expires_at)
        encrypted = self._encrypt(json.dumps(data))
        self._redis.set(self._token_key(user_id), encrypted)

    def get_token(self, user_id: str) -> Optional[Dict[str, str]]:
        blob = self._redis.get(self._token_key(user_id))
        if not blob:
            return None
        decrypted = self._decrypt(blob)
        return json.loads(decrypted)

    def delete_token(self, user_id: str) -> None:
        self._redis.delete(self._token_key(user_id))

    def iter_tokens(self) -> Iterable[tuple[str, Dict[str, str]]]:
        """Yield ``(user_id, token_data)`` for all stored tokens."""
        pattern = self._token_key("*")
        for key in self._redis.scan_iter(match=pattern):
            blob = self._redis.get(key)
            if not blob:
                continue
            user_id = key.split(":", 1)[1]
            data = json.loads(self._decrypt(cast(str, blob)))
            yield user_id, cast(Dict[str, str], data)

    # --- Escalation Flags --------------------------------------------

    def flag_escalation(self, call_sid: str) -> None:
        """Mark that the call requires escalation."""
        self.update_session(call_sid, escalation_required="true")

    def is_escalation_required(self, call_sid: str) -> bool:
        """Return ``True`` if escalation was requested for this call."""
        value = self.get_session(call_sid).get("escalation_required")
        return str(value).lower() == "true"

    # --- OAuth State -------------------------------------------------

    def set_oauth_state(self, state: str, user_id: str, ttl: int = 600) -> None:
        """Persist temporary mapping of OAuth state to user id."""
        self._redis.set(self._oauth_key(state), user_id, ex=ttl)

    def pop_oauth_state(self, state: str) -> Optional[str]:
        """Return user id for state and delete the key."""
        with self._redis.pipeline() as pipe:
            pipe.get(self._oauth_key(state))
            pipe.delete(self._oauth_key(state))
            user_id, _ = pipe.execute()
        return cast(Optional[str], user_id)

    # --- Conversation History ---------------------------------------

    def append_history(self, call_sid: str, speaker: str, text: str) -> None:
        """Append an entry to the conversation history."""
        key = self._key(call_sid)
        while True:
            pipe = self._redis.pipeline()
            try:
                pipe.watch(key)
                history_json = pipe.hget(key, "history")
                history: List[Dict[str, str]]
                if history_json:
                    history = cast(List[Dict[str, str]], json.loads(history_json))
                else:
                    history = []
                history.append({"speaker": speaker, "text": text})
                pipe.multi()
                pipe.hset(key, "history", json.dumps(history))
                pipe.execute()
                break
            except redis.WatchError:
                continue
            finally:
                pipe.reset()
        # A websocket listener can subscribe to transcript lines if desired.

    def get_history(self, call_sid: str) -> List[Dict[str, str]]:
        """Return conversation history for a call."""
        history_json = self._redis.hget(self._key(call_sid), "history")
        if not history_json:
            return []
        return cast(List[Dict[str, str]], json.loads(history_json))

    def set_summary(
        self, call_sid: str, summary: str, from_number: str | None = None
    ) -> None:
        """Store a summary for later handoff and vector recall."""
        self._redis.hset(self._key(call_sid), mapping={"summary": summary})
        metadata = [{"from_number": from_number}] if from_number else None
        self._summary_db.add_texts(
            [summary],
            ids=[call_sid],
            metadatas=metadata,
        )

    def get_summary(self, call_sid: str) -> Optional[str]:
        """Return saved summary if available."""
        return cast(Optional[str], self._redis.hget(self._key(call_sid), "summary"))

    def get_similar_summaries(self, text: str, n_results: int = 3) -> List[str]:
        """Return summaries semantically similar to ``text``."""
        return self._summary_db.search(text, n_results=n_results)
