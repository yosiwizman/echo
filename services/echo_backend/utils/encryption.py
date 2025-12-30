import base64
import os
import struct
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# ---------------------------------------------------------------------------
# Strict-mode flags: when set, missing encryption secret raises at init time.
# Default (CI/dev): secret is optional; errors only when encrypt/decrypt is used.
# ---------------------------------------------------------------------------
_REQUIRE_SECRETS = os.environ.get('ECHO_REQUIRE_SECRETS', '').lower() in ('1', 'true')
_REQUIRE_ENCRYPTION = os.environ.get('ECHO_REQUIRE_ENCRYPTION', '').lower() in ('1', 'true') or _REQUIRE_SECRETS

# Lazy-loaded encryption secret (validated on first use)
_encryption_secret: Optional[bytes] = None
_encryption_secret_loaded: bool = False


def _get_encryption_secret() -> bytes:
    """Return the encryption secret, validating and caching on first call.

    Raises:
        ValueError: If secret is missing/too short and strict mode is enabled,
                    or when actually called without a valid secret.
    """
    global _encryption_secret, _encryption_secret_loaded

    if not _encryption_secret_loaded:
        secret = os.getenv('ENCRYPTION_SECRET', '').encode('utf-8')
        if not secret or len(secret) < 32:
            if _REQUIRE_ENCRYPTION:
                raise ValueError(
                    "ENCRYPTION_SECRET environment variable not set or is too short. "
                    "It must be a securely managed 32-byte key."
                )
            # In non-strict mode, leave _encryption_secret as None
            _encryption_secret = None
        else:
            _encryption_secret = secret
        _encryption_secret_loaded = True

    if _encryption_secret is None:
        raise ValueError(
            "ENCRYPTION_SECRET environment variable not set or is too short. "
            "It must be a securely managed 32-byte key. "
            "Encryption functions cannot be used without a valid secret."
        )

    return _encryption_secret


# Backward-compat: ENCRYPTION_SECRET is now accessed via getter.
# Code that reads ENCRYPTION_SECRET directly will get this lazy property.
class _LazySecret:
    """Proxy that defers secret loading until accessed."""

    def __bytes__(self) -> bytes:
        return _get_encryption_secret()

    def __len__(self) -> int:
        return len(_get_encryption_secret())

    def __bool__(self) -> bool:
        try:
            return bool(_get_encryption_secret())
        except ValueError:
            return False


ENCRYPTION_SECRET = _LazySecret()  # type: ignore[assignment]


def derive_key(uid: str) -> bytes:
    """
    Derives a user-specific 32-byte key from the master secret and user ID (salt).
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=uid.encode('utf-8'),
        info=b'user-data-encryption',
    )
    return hkdf.derive(_get_encryption_secret())


def encrypt(data: str, uid: str) -> str:
    """
    Encrypts a string using a user-specific key.
    Returns a base64 encoded string containing nonce + ciphertext + tag.
    """
    if not data:
        return data
    key = derive_key(uid)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # GCM standard nonce size

    # Data must be bytes
    plaintext_bytes = data.encode('utf-8')

    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)

    # Combine nonce and ciphertext for storage
    encrypted_payload = nonce + ciphertext

    return base64.b64encode(encrypted_payload).decode('utf-8')


def decrypt(encrypted_data: str, uid: str) -> str:
    """
    Decrypts a base64 encoded string using a user-specific key.
    """
    if not encrypted_data or not isinstance(encrypted_data, str):
        return encrypted_data

    try:
        key = derive_key(uid)
        aesgcm = AESGCM(key)

        encrypted_payload = base64.b64decode(encrypted_data.encode('utf-8'))

        # Extract nonce and ciphertext
        nonce = encrypted_payload[:12]
        ciphertext = encrypted_payload[12:]

        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # If decryption fails (e.g., wrong key, corrupted data), return the original encrypted data
        # to avoid data loss and to make debugging easier. In a production system, you might want
        # to log this error.
        print(f"Decryption failed for user {uid}: {e}")
        return encrypted_data


def encrypt_audio_chunk(data: bytes, uid: str) -> bytes:
    """
    Encrypt audio chunk and return length-prefixed binary format.
    Format: [4 bytes length][12 bytes nonce][ciphertext + tag]

    This format allows concatenating multiple encrypted chunks without decryption.
    """
    key = derive_key(uid)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)

    # Encrypt (includes authentication tag)
    ciphertext = aesgcm.encrypt(nonce, data, None)

    # Combine nonce + ciphertext
    encrypted_payload = nonce + ciphertext

    # Add length prefix (4 bytes, big-endian)
    length = len(encrypted_payload)
    return struct.pack('>I', length) + encrypted_payload


def decrypt_audio_chunk(encrypted_data: bytes, uid: str, offset: int = 0):
    """
    Decrypt a single length-prefixed chunk.
    Returns: (decrypted_data, bytes_consumed)
    """
    # Read length prefix
    length = struct.unpack('>I', encrypted_data[offset : offset + 4])[0]
    offset += 4

    # Extract encrypted payload
    encrypted_payload = encrypted_data[offset : offset + length]

    # Extract nonce and ciphertext
    nonce = encrypted_payload[:12]
    ciphertext = encrypted_payload[12:]

    # Decrypt
    key = derive_key(uid)
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)

    return decrypted, 4 + length


def decrypt_audio_file(encrypted_data: bytes, uid: str) -> bytes:
    """
    Decrypt an entire merged audio file (multiple concatenated chunks).
    Each chunk is length-prefixed, allowing simple concatenation during merge.
    """
    decrypted_audio = bytearray()
    offset = 0

    while offset < len(encrypted_data):
        chunk_data, bytes_consumed = decrypt_audio_chunk(encrypted_data, uid, offset)
        decrypted_audio.extend(chunk_data)
        offset += bytes_consumed

    return bytes(decrypted_audio)
