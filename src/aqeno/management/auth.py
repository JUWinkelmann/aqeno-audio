"""Human-facing local administration authentication.

Listening profiles are intentionally absent: this protects the replaceable
Management UI and has no relationship to a listening context.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import stat
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from aqeno.ports.input import InputBus, InputEvent, Next, Previous, TogglePlayback

PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = 1024
SESSION_LIFETIME_SECONDS = 12 * 60 * 60
CONFIRMATION_LIFETIME_SECONDS = 90
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
_CONFIRMATION_SEQUENCE = (Previous, TogglePlayback, Next)


class AuthError(RuntimeError):
    code = "auth_error"


class PasswordInvalidError(AuthError):
    code = "password_incorrect"


class PasswordPolicyError(AuthError):
    code = "password_policy"


class SetupStateError(AuthError):
    code = "setup_state_invalid"


class ConfirmationError(AuthError):
    code = "physical_confirmation_required"


class RateLimitError(AuthError):
    code = "auth_rate_limited"

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("too many attempts")
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True, slots=True)
class PasswordRecord:
    format_version: int
    algorithm: str
    salt: str
    digest: str
    n: int
    r: int
    p: int


@dataclass(frozen=True, slots=True)
class Session:
    token_hash: str
    csrf_token: str
    expires_at: float


@dataclass(frozen=True, slots=True)
class PhysicalConfirmation:
    id: uuid.UUID
    purpose: str
    expires_at: float
    confirmed: bool = False
    sequence_position: int = 0


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.partial")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


class PasswordStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def configured(self) -> bool:
        return self.path.is_file()

    def _record(self) -> PasswordRecord:
        try:
            if self.path.is_symlink() or stat.S_IMODE(self.path.stat().st_mode) & 0o077:
                raise SetupStateError("admin credential permissions are unsafe")
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            record = PasswordRecord(**raw)
        except SetupStateError:
            raise
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SetupStateError("admin credential is unreadable") from exc
        if (
            record.format_version != 1
            or record.algorithm != "scrypt"
            or (record.n, record.r, record.p) != (SCRYPT_N, SCRYPT_R, SCRYPT_P)
        ):
            raise SetupStateError("admin credential format is unsupported")
        return record

    @staticmethod
    def _validate_policy(password: str) -> None:
        if len(password) < PASSWORD_MIN_LENGTH:
            raise PasswordPolicyError(
                f"password must have at least {PASSWORD_MIN_LENGTH} characters"
            )
        if len(password) > PASSWORD_MAX_LENGTH:
            raise PasswordPolicyError(f"password may have at most {PASSWORD_MAX_LENGTH} characters")

    def set(self, password: str) -> None:
        self._validate_policy(password)
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
        )
        record = PasswordRecord(
            format_version=1,
            algorithm="scrypt",
            salt=base64.b64encode(salt).decode("ascii"),
            digest=base64.b64encode(digest).decode("ascii"),
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
        )
        _atomic_json(self.path, asdict(record))

    def verify(self, password: str) -> bool:
        record = self._record()
        try:
            salt = base64.b64decode(record.salt, validate=True)
            expected = base64.b64decode(record.digest, validate=True)
            if len(salt) != 16 or len(expected) != 64:
                raise ValueError("invalid credential payload")
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=record.n,
                r=record.r,
                p=record.p,
            )
        except (ValueError, TypeError) as exc:
            raise SetupStateError("admin credential is unreadable") from exc
        return hmac.compare_digest(actual, expected)


class AttemptLimiter:
    def __init__(self, *, now: Callable[[], float] = time.monotonic) -> None:
        self._now = now
        self._attempts: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def check(self, peer: str) -> None:
        with self._lock:
            failures, blocked_until = self._attempts.get(peer, (0, 0.0))
            remaining = blocked_until - self._now()
            if remaining > 0:
                raise RateLimitError(max(1, int(remaining + 0.999)))
            if failures == 0:
                self._attempts.pop(peer, None)

    def failed(self, peer: str) -> None:
        with self._lock:
            failures, _ = self._attempts.get(peer, (0, 0.0))
            failures += 1
            delay = 0 if failures < 5 else min(60, 2 ** (failures - 5))
            self._attempts[peer] = (failures, self._now() + delay)

    def succeeded(self, peer: str) -> None:
        with self._lock:
            self._attempts.pop(peer, None)


class AdminAuth:
    def __init__(
        self,
        *,
        credential_path: Path,
        inputs: InputBus,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self.passwords = PasswordStore(credential_path)
        self._now = now
        self._sessions: dict[str, Session] = {}
        self._confirmation: PhysicalConfirmation | None = None
        self._lock = threading.RLock()
        self.limiter = AttemptLimiter(now=now)
        inputs.on_input(self._handle_input)

    @property
    def configured(self) -> bool:
        return self.passwords.configured()

    def begin_confirmation(self, purpose: str) -> PhysicalConfirmation:
        if purpose not in {"setup", "recovery"}:
            raise ValueError(purpose)
        with self._lock:
            current = self._confirmation
            if (
                current is not None
                and current.purpose == purpose
                and current.expires_at > self._now()
            ):
                return current
            confirmation = PhysicalConfirmation(
                id=uuid.uuid4(),
                purpose=purpose,
                expires_at=self._now() + CONFIRMATION_LIFETIME_SECONDS,
            )
            self._confirmation = confirmation
        return confirmation

    def confirm(self, confirmation_id: uuid.UUID, purpose: str) -> PhysicalConfirmation:
        """Confirm through an already authenticated machine/recovery boundary."""
        with self._lock:
            current = self._confirmation
            if (
                current is None
                or current.id != confirmation_id
                or current.purpose != purpose
                or current.expires_at <= self._now()
            ):
                raise ConfirmationError("physical confirmation is missing or expired")
            confirmed = PhysicalConfirmation(
                current.id,
                current.purpose,
                current.expires_at,
                True,
                len(_CONFIRMATION_SEQUENCE),
            )
            self._confirmation = confirmed
        return confirmed

    def confirmation(self, confirmation_id: uuid.UUID, purpose: str) -> PhysicalConfirmation:
        with self._lock:
            current = self._confirmation
            if (
                current is None
                or current.id != confirmation_id
                or current.purpose != purpose
                or current.expires_at <= self._now()
            ):
                raise ConfirmationError("physical confirmation is missing or expired")
            return current

    def consume_confirmation(self, confirmation_id: uuid.UUID, purpose: str) -> None:
        with self._lock:
            current = self._confirmation
            if (
                current is None
                or current.id != confirmation_id
                or current.purpose != purpose
                or current.expires_at <= self._now()
            ):
                raise ConfirmationError("physical confirmation is missing or expired")
            if not current.confirmed:
                raise ConfirmationError("physical confirmation is still pending")
            self._confirmation = None

    def _handle_input(self, event: InputEvent) -> None:
        if not isinstance(event, _CONFIRMATION_SEQUENCE):
            return
        with self._lock:
            current = self._confirmation
            if current is None or current.expires_at <= self._now() or current.confirmed:
                return
            expected = _CONFIRMATION_SEQUENCE[current.sequence_position]
            position = current.sequence_position + 1 if isinstance(event, expected) else 0
            if position == 0 and isinstance(event, _CONFIRMATION_SEQUENCE[0]):
                position = 1
            self._confirmation = PhysicalConfirmation(
                current.id,
                current.purpose,
                current.expires_at,
                position == len(_CONFIRMATION_SEQUENCE),
                position,
            )

    def create_initial_password(
        self, confirmation_id: uuid.UUID, password: str
    ) -> tuple[str, Session]:
        if self.configured:
            raise SetupStateError("administration is already configured")
        self.consume_confirmation(confirmation_id, "setup")
        self.passwords.set(password)
        return self.create_session()

    def recover(self, confirmation_id: uuid.UUID, password: str) -> tuple[str, Session]:
        if not self.configured:
            raise SetupStateError("administration is not configured")
        self.consume_confirmation(confirmation_id, "recovery")
        self.passwords.set(password)
        self.revoke_all()
        return self.create_session()

    def login(self, password: str, peer: str) -> tuple[str, Session]:
        if not self.configured:
            raise SetupStateError("administration setup is required")
        self.limiter.check(peer)
        if not self.passwords.verify(password):
            self.limiter.failed(peer)
            raise PasswordInvalidError("password is incorrect")
        self.limiter.succeeded(peer)
        return self.create_session()

    def change_password(self, current: str, new: str) -> None:
        if not self.passwords.verify(current):
            raise PasswordInvalidError("password is incorrect")
        self.passwords.set(new)
        self.revoke_all()

    def create_session(self) -> tuple[str, Session]:
        token = secrets.token_urlsafe(32)
        session = Session(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            csrf_token=secrets.token_urlsafe(24),
            expires_at=self._now() + SESSION_LIFETIME_SECONDS,
        )
        with self._lock:
            expired = [
                key for key, value in self._sessions.items() if value.expires_at <= self._now()
            ]
            for key in expired:
                self._sessions.pop(key, None)
            self._sessions[session.token_hash] = session
        return token, session

    def session(self, token: str | None) -> Session | None:
        if not token:
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None or session.expires_at <= self._now():
                self._sessions.pop(token_hash, None)
                return None
            return session

    def revoke(self, token: str | None) -> None:
        if token:
            with self._lock:
                self._sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)

    def revoke_all(self) -> None:
        with self._lock:
            self._sessions.clear()
