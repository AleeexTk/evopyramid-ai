"""EvoAGIKeyManager provides lifecycle management for AGI access keys.

The implementation favours simplicity and determinism so tests can exercise
core behaviours without relying on heavy cryptographic libraries. The manager
persists key metadata, offers symmetric encryption, tracks token usage, and
creates rolling backups for resilience.
"""

from __future__ import annotations

import base64
import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
import hashlib
import uuid


class EvoAGIKeyManager:
    """Manage AGI keys, encryption modes, and lifecycle events."""

    _REMOVABLE_STATUSES = {"expired", "revoked", "token_limit_exceeded", "decryption_failed", "error"}

    def __init__(
        self,
        master_key: str,
        key_storage_file: str = "evo_agi_keys.json",
        *,
        encrypt_full_storage: bool = True,
    ) -> None:
        if not master_key:
            raise ValueError("master_key must be provided")
        self.master_key = master_key
        self.key_storage_file = key_storage_file
        self.encrypt_full_storage = encrypt_full_storage
        self._lock = threading.RLock()
        self.keys: Dict[str, Dict[str, object]] = {}
        self._load_keys()

    # ------------------------------------------------------------------
    # Persistence helpers
    def _load_keys(self) -> None:
        if not os.path.exists(self.key_storage_file):
            return
        try:
            with open(self.key_storage_file, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError:
            # Corrupted storage is treated as empty but preserved for forensics.
            return

        storage_mode = payload.get("encrypt_full_storage")
        if storage_mode is not None:
            self.encrypt_full_storage = bool(storage_mode)
        self.keys = payload.get("keys", {})

    def _serialise(self) -> Dict[str, object]:
        return {
            "encrypt_full_storage": self.encrypt_full_storage,
            "keys": self.keys,
        }

    def _create_backup(self, payload: Dict[str, object]) -> Optional[str]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_path = f"{self.key_storage_file}.{timestamp}.bak"
        try:
            with open(backup_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        except OSError:
            return None
        return backup_path

    def save_keys(self) -> str:
        """Persist current keys and create a backup snapshot."""
        with self._lock:
            payload = self._serialise()
            self._create_backup(payload)
            with open(self.key_storage_file, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        return self.key_storage_file

    # ------------------------------------------------------------------
    # Encryption helpers
    def _derive_keystream(self, length: int) -> bytes:
        seed = hashlib.sha256(self.master_key.encode("utf-8")).digest()
        stream = bytearray()
        counter = 0
        while len(stream) < length:
            counter_bytes = counter.to_bytes(4, "big")
            seed = hashlib.sha256(seed + counter_bytes).digest()
            stream.extend(seed)
            counter += 1
        return bytes(stream[:length])

    def encrypt_value(self, value: object) -> str:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        data = text.encode("utf-8")
        if not data:
            return ""
        keystream = self._derive_keystream(len(data))
        encrypted = bytes(b ^ k for b, k in zip(data, keystream))
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_value(self, encrypted_value: str) -> Optional[str]:
        if encrypted_value == "":
            return ""
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode("utf-8"))
        except Exception:
            return None
        keystream = self._derive_keystream(len(encrypted_bytes))
        decrypted_bytes = bytes(b ^ k for b, k in zip(encrypted_bytes, keystream))
        try:
            return decrypted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return None

    # ------------------------------------------------------------------
    # Public API
    def list_keys(self) -> Dict[str, Dict[str, object]]:
        return dict(self.keys)

    def generate_agi_key(
        self,
        resource: str,
        user: str,
        *,
        token_limit: Optional[int] = None,
        notes: Optional[str] = None,
        auto_renew: bool = False,
    ) -> str:
        with self._lock:
            key_id = f"agi_{uuid.uuid4().hex[:12]}"
            raw_key = f"sk-{resource}-{uuid.uuid4().hex}"
            encrypted_value = self.encrypt_value(raw_key)
            entry = {
                "resource": resource,
                "user": user,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "token_limit": token_limit,
                "token_used": 0,
                "status": "active",
                "auto_renew": auto_renew,
                "notes": notes,
                "key_value": encrypted_value,
            }
            if not self.encrypt_full_storage:
                entry["key_value_plain"] = raw_key
            self.keys[key_id] = entry
            self.save_keys()
            return key_id

    def get_key_value(self, key_id: str) -> Optional[str]:
        key_data = self.keys.get(key_id)
        if not key_data:
            return None
        stored_value = key_data.get("key_value", "")
        decrypted = self.decrypt_value(stored_value if isinstance(stored_value, str) else "")
        if decrypted is None:
            key_data["status"] = "decryption_failed"
            self.save_keys()
            return None
        if not self.encrypt_full_storage:
            key_data["key_value_plain"] = decrypted
        return decrypted

    def validate_key(self, key_id: str, *, token_cost: int = 0) -> Tuple[bool, str]:
        key_data = self.keys.get(key_id)
        if not key_data:
            return False, "Key not found"

        value = self.get_key_value(key_id)
        if value is None:
            return False, "Key decryption failed"

        status = key_data.get("status", "active")
        if status not in {"active", "token_limit_exceeded"}:
            return False, f"Key status is {status}"

        limit = key_data.get("token_limit")
        used = key_data.get("token_used", 0)
        if limit is not None and used + token_cost > limit:
            key_data["token_used"] = used + token_cost
            key_data["status"] = "token_limit_exceeded"
            self.save_keys()
            return False, "Token limit exceeded"

        key_data["token_used"] = used + token_cost
        key_data["status"] = "active"
        self.save_keys()
        return True, "Key valid"

    def reset_token_usage(self, key_id: str) -> bool:
        key_data = self.keys.get(key_id)
        if not key_data:
            return False
        key_data["token_used"] = 0
        key_data["status"] = "active"
        self.save_keys()
        return True

    def change_encryption_mode(self, enable_encryption: bool) -> None:
        if enable_encryption == self.encrypt_full_storage:
            return
        with self._lock:
            if enable_encryption:
                for key_data in self.keys.values():
                    plain = key_data.pop("key_value_plain", None)
                    if plain is not None:
                        key_data["key_value"] = self.encrypt_value(plain)
            else:
                for key_data in self.keys.values():
                    stored_value = key_data.get("key_value", "")
                    decrypted = self.decrypt_value(stored_value if isinstance(stored_value, str) else "")
                    if decrypted is None:
                        key_data["status"] = "decryption_failed"
                    else:
                        key_data["key_value_plain"] = decrypted
            self.encrypt_full_storage = enable_encryption
            self.save_keys()

    def cleanup_keys(self) -> int:
        removed = 0
        with self._lock:
            for key_id in list(self.keys.keys()):
                key_data = self.keys[key_id]
                status = key_data.get("status", "active")
                auto_renew = bool(key_data.get("auto_renew"))
                if status in self._REMOVABLE_STATUSES and not auto_renew:
                    del self.keys[key_id]
                    removed += 1
            if removed:
                self.save_keys()
        return removed
