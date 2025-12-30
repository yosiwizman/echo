import hashlib
import json
import os
import uuid
from typing import Optional

from google.cloud import firestore

# Lazy-initialized Firestore client (avoid ADC errors at import time in CI)
_db: Optional[firestore.Client] = None


def _ensure_credentials_file() -> None:
    """Write SERVICE_ACCOUNT_JSON to disk if present (one-time)."""
    if os.environ.get('SERVICE_ACCOUNT_JSON'):
        service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
        with open('google-credentials.json', 'w') as f:
            json.dump(service_account_info, f)


def get_db() -> firestore.Client:
    """Return the Firestore client, creating it lazily on first call."""
    global _db
    if _db is None:
        _ensure_credentials_file()
        _db = firestore.Client()
    return _db


# Backward-compat alias – existing code imports `db` directly.
# This is a lazy proxy that defers client creation until first attribute access.
class _LazyDB:
    def __getattr__(self, name):
        return getattr(get_db(), name)


db = _LazyDB()


def get_users_uid():
    users_ref = get_db().collection('users')
    return [str(doc.id) for doc in users_ref.stream()]


def document_id_from_seed(seed: str) -> uuid.UUID:
    """Avoid repeating the same data"""
    seed_hash = hashlib.sha256(seed.encode('utf-8')).digest()
    generated_uuid = uuid.UUID(bytes=seed_hash[:16], version=4)
    return str(generated_uuid)
