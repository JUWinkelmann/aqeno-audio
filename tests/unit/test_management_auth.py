from __future__ import annotations

import json
from pathlib import Path

import pytest

from aqeno.adapters.fakes.input import FakeInputBus
from aqeno.management.auth import (
    AdminAuth,
    ConfirmationError,
    PasswordInvalidError,
    PasswordPolicyError,
    SetupStateError,
)
from aqeno.ports.input import Next, Previous, TogglePlayback


class MutableNow:
    value = 100.0

    def __call__(self) -> float:
        return self.value


def test_password_is_scrypt_hashed_and_never_persisted_as_plaintext(tmp_path: Path) -> None:
    inputs = FakeInputBus()
    path = tmp_path / "secrets" / "admin-auth.json"
    auth = AdminAuth(credential_path=path, inputs=inputs)
    confirmation = auth.begin_confirmation("setup")
    inputs.emit(Previous())
    inputs.emit(TogglePlayback())
    inputs.emit(Next())
    auth.create_initial_password(confirmation.id, "meine lange passphrase")

    payload = path.read_text(encoding="utf-8")
    record = json.loads(payload)
    assert "meine lange passphrase" not in payload
    assert record["algorithm"] == "scrypt"
    assert record["format_version"] == 1
    assert path.stat().st_mode & 0o777 == 0o600


def test_password_policy_is_passphrase_friendly_without_character_rules(tmp_path: Path) -> None:
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=FakeInputBus())
    with pytest.raises(PasswordPolicyError):
        auth.passwords.set("zu kurz")
    auth.passwords.set("nur kleine wörter sind erlaubt")
    assert auth.passwords.verify("nur kleine wörter sind erlaubt")


def test_credential_with_unsafe_permissions_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "auth.json"
    auth = AdminAuth(credential_path=path, inputs=FakeInputBus())
    auth.passwords.set("eine sichere passphrase")
    path.chmod(0o644)
    with pytest.raises(SetupStateError, match="permissions are unsafe"):
        auth.passwords.verify("eine sichere passphrase")


def test_confirmation_requires_deliberate_hardware_sequence_and_expires(tmp_path: Path) -> None:
    now = MutableNow()
    inputs = FakeInputBus()
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=inputs, now=now)
    confirmation = auth.begin_confirmation("setup")
    inputs.emit(Next())
    assert auth.confirmation(confirmation.id, "setup").confirmed is False
    inputs.emit(Previous())
    inputs.emit(TogglePlayback())
    assert auth.confirmation(confirmation.id, "setup").confirmed is False
    inputs.emit(Next())
    assert auth.confirmation(confirmation.id, "setup").confirmed is True

    confirmation = auth.begin_confirmation("setup")
    now.value += 91
    with pytest.raises(ConfirmationError):
        auth.confirmation(confirmation.id, "setup")


def test_repeated_confirmation_start_cannot_replace_an_active_challenge(tmp_path: Path) -> None:
    now = MutableNow()
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=FakeInputBus(), now=now)
    first = auth.begin_confirmation("setup")
    assert auth.begin_confirmation("setup") == first


def test_session_tokens_are_stored_only_as_hashes_and_expire(tmp_path: Path) -> None:
    now = MutableNow()
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=FakeInputBus(), now=now)
    token, session = auth.create_session()
    assert token != session.token_hash
    assert auth.session(token) == session
    now.value = session.expires_at + 1
    assert auth.session(token) is None


def test_password_change_checks_current_password_and_revokes_existing_sessions(
    tmp_path: Path,
) -> None:
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=FakeInputBus())
    auth.passwords.set("altes passwort")
    token, _ = auth.create_session()
    with pytest.raises(PasswordInvalidError):
        auth.change_password("falsch falsch", "neues passwort")
    auth.change_password("altes passwort", "neues passwort")
    assert auth.session(token) is None
    assert auth.passwords.verify("neues passwort")


def test_failed_authentication_never_logs_password_material(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    auth = AdminAuth(credential_path=tmp_path / "auth.json", inputs=FakeInputBus())
    auth.passwords.set("richtiges testpasswort")
    attempted = "falsches geheimes testpasswort"
    with pytest.raises(PasswordInvalidError):
        auth.login(attempted, "local-test")
    assert attempted not in caplog.text
