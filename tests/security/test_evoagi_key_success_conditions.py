"""Success-condition tests for the EvoAGIKeyManager."""

from __future__ import annotations

import os
import sys
import pytest

# Ensure the repository root is on the import path.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from apps.core.security.EvoAGIKey import EvoAGIKeyManager  # noqa: E402


@pytest.fixture
def manager(tmp_path):
    """Create a manager instance inside a temporary directory."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    mgr = EvoAGIKeyManager("test-master-key", encrypt_full_storage=False)
    yield mgr
    os.chdir(old_cwd)


@pytest.mark.evo_success_condition
def test_encrypt_decrypt_symmetry(manager):
    """Values should round-trip through the encryption helpers."""
    test_values = ["secret123", "sk-real-openai-key-789", "", "special-chars-!@#$%"]

    for value in test_values:
        encrypted = manager.encrypt_value(value)
        decrypted = manager.decrypt_value(encrypted)
        assert decrypted == value, f"Failed for value: {value!r}"


@pytest.mark.evo_success_condition
def test_token_limit_and_reset(manager):
    """Token accounting should enforce limits and allow resets."""
    key_id = manager.generate_agi_key(
        "openai",
        "test_user",
        token_limit=100,
        notes="Test token limit functionality",
    )

    is_valid, msg = manager.validate_key(key_id, token_cost=90)
    assert is_valid, f"Key should be valid after 90 tokens: {msg}"
    assert manager.keys[key_id]["token_used"] == 90

    is_valid, msg = manager.validate_key(key_id, token_cost=20)
    assert not is_valid, "Key should be invalid after exceeding token limit"
    assert manager.keys[key_id]["status"] == "token_limit_exceeded"
    assert manager.keys[key_id]["token_used"] == 110

    reset_success = manager.reset_token_usage(key_id)
    assert reset_success, "Token reset should succeed"
    assert manager.keys[key_id]["token_used"] == 0
    assert manager.keys[key_id]["status"] == "active"

    is_valid, msg = manager.validate_key(key_id, token_cost=50)
    assert is_valid, f"Key should be valid after reset: {msg}"


@pytest.mark.evo_success_condition
def test_encryption_mode_switch(manager):
    """Switching encryption modes must preserve stored keys."""
    initial_mode = manager.encrypt_full_storage

    manager.change_encryption_mode(not initial_mode)
    assert manager.encrypt_full_storage is not initial_mode

    test_kid = manager.generate_agi_key("google", "switch_test_user")
    assert test_kid in manager.keys

    manager.change_encryption_mode(initial_mode)
    assert manager.encrypt_full_storage == initial_mode
    assert test_kid in manager.keys


@pytest.mark.evo_success_condition
def test_jsondecode_and_token_errors(manager):
    """Corrupted ciphertext should fail gracefully."""
    key_id = manager.generate_agi_key("google", "err_user")
    original_status = manager.keys[key_id]["status"]
    assert original_status == "active"

    manager.keys[key_id]["key_value"] = "corrupted_encrypted_data!"

    decrypted_value = manager.get_key_value(key_id)
    assert decrypted_value is None, "Should return None for corrupted data"
    assert manager.keys[key_id]["status"] in {"decryption_failed", "error"}

    is_valid, msg = manager.validate_key(key_id)
    assert not is_valid, "Validation should fail with corrupted key value"
    assert "decryption" in msg.lower() or "error" in msg.lower()


@pytest.mark.evo_success_condition
def test_backup_creation_on_save(manager):
    """Saving should create a .bak snapshot alongside the main file."""
    for i in range(3):
        manager.generate_agi_key("openai", f"user_{i}")

    initial_files = set(os.listdir())
    manager.save_keys()
    final_files = set(os.listdir())

    backup_files = [f for f in final_files - initial_files if f.endswith(".bak")]
    if not backup_files:
        backup_files = [f for f in final_files if f.endswith(".bak")]
    assert backup_files, "Should create backup file on save"
    assert manager.key_storage_file in final_files


@pytest.mark.evo_success_condition
def test_cleanup_obsolete_keys(manager):
    """Expired keys without auto-renew should be removed."""
    active_kid = manager.generate_agi_key("openai", "active_user", auto_renew=True)
    expired_kid = manager.generate_agi_key("google", "expired_user", auto_renew=False)

    manager.keys[expired_kid]["status"] = "expired"

    initial_count = len(manager.keys)
    removed = manager.cleanup_keys()

    assert removed >= 1
    assert len(manager.keys) < initial_count
    assert active_kid in manager.keys
    assert expired_kid not in manager.keys
