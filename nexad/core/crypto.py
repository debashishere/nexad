"""core/crypto.py — AES-256-GCM encryption and HMAC-SHA256 signature utilities.

Pure-Python; no DB or Redis dependency. Safe to import from any service.
"""

import base64
import hashlib
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from nexad.core.config import get_settings

# ---------------------------------------------------------------------------
# Module-level key loading
# ---------------------------------------------------------------------------

try:
    _hex_key: str = get_settings().AES_SECRET_KEY
except Exception:
    # Allow deferred failure during testing when Settings is not fully hydrated.
    _hex_key = ""

def _validate_aes_key(raw_key: bytes) -> bytes:
    """Validate that *raw_key* is exactly 32 bytes; raise ``ValueError`` otherwise.

    Extracted so tests can call the validation path directly without re-importing
    the module (which would require env-var manipulation).
    """
    if len(raw_key) != 32:
        raise ValueError(
            f"AES_SECRET_KEY must decode to exactly 32 bytes (256 bits); "
            f"got {len(raw_key)} bytes. "
            "Set AES_SECRET_KEY to a 64-character lowercase hex string."
        )
    return raw_key


if _hex_key:
    AES_SECRET_KEY: bytes = _validate_aes_key(bytes.fromhex(_hex_key))
else:
    AES_SECRET_KEY = b""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def encrypt_token(plaintext: str, secret_key: bytes) -> tuple[str, str, str]:
    """Encrypt *plaintext* with AES-256-GCM.

    Args:
        plaintext: The UTF-8 string to encrypt (e.g. an OAuth refresh token).
        secret_key: A 32-byte AES key.

    Returns:
        A 3-tuple ``(ciphertext_b64, iv_hex, tag_hex)`` where
        *ciphertext_b64* is Base-64-encoded ciphertext (tag appended by AESGCM),
        *iv_hex* is the 12-byte IV as a hex string, and
        *tag_hex* is the 16-byte authentication tag as a hex string.
    """
    iv = os.urandom(12)  # 96-bit nonce — recommended for AES-GCM
    aesgcm = AESGCM(secret_key)
    # AESGCM.encrypt() appends the 16-byte tag to the ciphertext.
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    # Split: last 16 bytes are the tag.
    ciphertext = ciphertext_with_tag[:-16]
    tag = ciphertext_with_tag[-16:]
    return (
        base64.b64encode(ciphertext).decode("ascii"),
        iv.hex(),
        tag.hex(),
    )


def decrypt_token(
    ciphertext_b64: str, iv_hex: str, tag_hex: str, secret_key: bytes
) -> str:
    """Decrypt a value previously encrypted by :func:`encrypt_token`.

    Args:
        ciphertext_b64: Base-64-encoded ciphertext (without the tag).
        iv_hex: Hex-encoded 12-byte IV used during encryption.
        tag_hex: Hex-encoded 16-byte GCM authentication tag.
        secret_key: The same 32-byte AES key used to encrypt.

    Returns:
        The original plaintext string.

    Raises:
        cryptography.exceptions.InvalidTag: If the ciphertext or tag has been
            tampered with.
    """
    ciphertext = base64.b64decode(ciphertext_b64)
    iv = bytes.fromhex(iv_hex)
    tag = bytes.fromhex(tag_hex)
    aesgcm = AESGCM(secret_key)
    # AESGCM.decrypt() expects ciphertext + tag concatenated.
    plaintext_bytes = aesgcm.decrypt(iv, ciphertext + tag, None)
    return plaintext_bytes.decode("utf-8")


def verify_hmac_signature(
    token: str, timestamp: str, incoming_sig: str, secret_key: str
) -> bool:
    """Verify a Slack HITL approval callback signature.

    Implements the Slack signing formula exactly as specified in the LLD:
    ``v0:{timestamp}:{token}`` signed with HMAC-SHA256.

    Args:
        token: The Action Token from the callback payload.
        timestamp: The ``X-Slack-Request-Timestamp`` header value.
        incoming_sig: The signature string to verify (hex digest, no prefix).
        secret_key: The Slack signing secret (UTF-8 string).

    Returns:
        ``True`` if the signature is valid; ``False`` otherwise.
    """
    message = f"v0:{timestamp}:{token}".encode("utf-8")
    expected_sig = hmac.new(
        secret_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_sig, incoming_sig)
